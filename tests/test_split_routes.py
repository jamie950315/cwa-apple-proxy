import ipaddress,pytest
from split_routes import approval_status,merge_routes,specific,configured_routes
from network_rules import render_rules,address_sets

MAC='100.122.163.78';MAC6='fd7a:115c:a1e0::eb36:a34f'
PI='100.78.140.101';PI6='fd7a:115c:a1e0::5901:8c9c'
TS={'Self':{'TailscaleIPs':[PI,PI6]},'Peer':{'mac':{'TailscaleIPs':[MAC,MAC6]}}}
CONFIG={'enabled':[{'ipv4':MAC}]}
ROUTES=['17.253.0.0/16','2620:149:a00::/40']

def test_exit_node_approval_does_not_approve_specific_routes():
 r=approval_status(ROUTES,{'AllowedIPs':['0.0.0.0/0','::/0',PI+'/32']})
 assert r['approved']==[] and r['pending']==ROUTES

def test_partial_subnet_approval_is_reported():
 r=approval_status(ROUTES,{'AllowedIPs':['0.0.0.0/0',ROUTES[0]]})
 assert r['approved']==[ROUTES[0]] and r['pending']==[ROUTES[1]]

def test_full_subnet_approval():
 assert not approval_status(ROUTES,{'AllowedIPs':ROUTES})['pending']

def test_merge_preserves_lan_other_routes_and_omits_default_set_flag():
 before=['0.0.0.0/0','::/0','192.168.31.0/24','10.2.0.0/16']
 assert merge_routes(before,ROUTES)==['192.168.31.0/24','10.2.0.0/16']+ROUTES

def test_remove_only_owned_routes():
 assert merge_routes(['192.168.31.0/24']+ROUTES,[],[ROUTES[0]])==['192.168.31.0/24',ROUTES[1]]

def test_merge_is_idempotent():
 a=merge_routes(['192.168.31.0/24'],ROUTES)
 assert merge_routes(a,ROUTES)==a

def test_selective_routes_are_narrow_and_cover_measured_addresses():
 n=[ipaddress.ip_network(p) for p in configured_routes()]
 for addr in ['17.253.87.61','17.253.145.10','17.253.150.10','2403:300:a04:2000::61','2620:149:af6::10','2a01:b740:a10:3000::21']:
  a=ipaddress.ip_address(addr);assert any(a.version==p.version and a in p for p in n)
 for addr in ['1.1.1.1','8.8.8.8','17.57.144.10','2001:4860:4860::8888']:
  a=ipaddress.ip_address(addr);assert not any(a.version==p.version and a in p for p in n)

def test_client_addresses_include_only_enrolled_peer():
 assert address_sets(CONFIG,TS)==([MAC],[MAC6])

def test_unenrolled_clients_have_no_reject_rule_elements():
 text=render_rules({'enabled':[]},TS,ROUTES)
 assert MAC not in text and MAC6 not in text

@pytest.mark.parametrize('bad',['1.1.1.1','127.0.0.1','100.78.140.101; drop','::1'])
def test_unsafe_client_input_rejected(bad):
 with pytest.raises(ValueError):render_rules({'enabled':[{'ipv4':bad}]},TS,ROUTES)

def test_firewall_targets_udp443_only_no_tcp_or_default_drop():
 text=render_rules(CONFIG,TS,ROUTES)
 rejects=[line for line in text.splitlines() if ' reject ' in line]
 assert len(rejects)==6
 assert all('@clients' in line and 'iifname "tailscale0"' in line for line in rejects)
 assert len([line for line in rejects if 'udp dport 443' in line])==5
 assert 'policy drop' not in text
 tcp=[line for line in rejects if 'tcp dport' in line]
 assert len(tcp)==1 and 'ip6 daddr @relay6' in tcp[0] and 'fib daddr oif missing' in tcp[0] and 'reject with tcp reset' in tcp[0]
 assert '@bridge4' in text and '@relay6' in text
 assert '17.0.0.0/8' not in text

def test_atomic_nft_replacement():
 assert render_rules(CONFIG,TS,ROUTES,True).startswith('delete table inet cwa_weather\ntable inet cwa_weather')

def test_dns_rules_preserve_opt_in_ipv4_ipv6_and_relay_alias():
 from bridgectl import rules_for
 rules=rules_for(CONFIG,list(TS['Peer'].values()))
 assert any('tether.v.aaplimg.com' in r for r in rules)
 assert all('client='+MAC+'|'+MAC6 in r for r in rules if not r.startswith('!'))
 assert any('dnsrewrite=NOERROR;A;'+PI in r for r in rules)


def test_ipv6_reject_precedes_destination_route_lookup():
 text=render_rules(CONFIG,TS,ROUTES)
 pre=text.split('chain prerouting {',1)[1].split('}\n',1)[0]
 assert 'hook prerouting' in pre
 assert 'udp dport 443' in pre and 'tcp dport 443 fib daddr oif missing' in pre
 assert 'ip saddr @clients4' not in pre
 assert '@clients6' in pre and '@relay6' in pre


def test_ipv6_tcp_guard_does_not_match_tailnet_or_other_ports():
 text=render_rules(CONFIG,TS,ROUTES)
 guard=next(line for line in text.splitlines() if 'reject with tcp reset' in line)
 assert 'ip6 daddr @relay6' in guard and 'tcp dport 443' in guard
 assert '@bridge6' not in guard


def test_restricted_dns_requires_all_four_exact_domains():
 from split_routes import restricted_dns_status,DNS_DOMAINS
 txt='\n'.join('  - '+d+' -> 100.78.140.101' for d in DNS_DOMAINS)
 assert restricted_dns_status(txt)['ready']
 assert not restricted_dns_status(txt.replace('tthr.apple.com','tthr.apple.com.invalid'))['ready']
 assert not restricted_dns_status(txt.replace('100.78.140.101','1.1.1.1',1))['ready']


def test_dns_status_extra_domains_preserved_and_no_order_assumption():
 from split_routes import restricted_dns_status,DNS_DOMAINS
 txt='  - ts.net. -> 199.247.155.53\n'+'\n'.join('  - '+d+'. -> 100.78.140.101' for d in reversed(DNS_DOMAINS))
 assert restricted_dns_status(txt)['ready']
