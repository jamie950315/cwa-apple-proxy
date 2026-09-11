from pathlib import Path
import time,shutil,json,subprocess
R=Path('/home/jamie/cwa-weather-proxy');D=R/'research/approved-split'
b=R/'backups'/('approved-split-'+str(int(time.time())));b.mkdir()
for name in ['network_rules.py','split_routes.py','tests/test_split_routes.py','dashboard.html','README.md','config/split-routing.json']:
 p=R/name;q=b/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
(D/'backup.txt').write_text(str(b))
p=R/'network_rules.py';s=p.read_text();needle='    text+=\'chain input { type filter hook input priority -10; policy accept;\\n\''
insert='''    # Reject before route lookup so missing public IPv6 egress cannot stall QUIC.
    # TCP IPv6 is rejected ONLY when the local FIB has no destination route.
    # A restored IPv6 uplink automatically makes the TCP guard stop matching.
    text+='chain prerouting { type filter hook prerouting priority -10; policy accept;\\n'
    text+='iifname "tailscale0" ip6 saddr @clients6 ip6 daddr @relay6 udp dport 443 counter reject with icmpx type port-unreachable comment "cwa IPv6 relay QUIC early fallback"\\n'
    text+='iifname "tailscale0" ip6 saddr @clients6 ip6 daddr @relay6 tcp dport 443 fib daddr oif missing counter reject with tcp reset comment "cwa IPv6 relay missing-uplink fast fallback"\\n}\\n'
'''
assert needle in s;s=s.replace(needle,insert+needle,1).replace("'transportVersion':'1.0.0'","'transportVersion':'1.0.1'")
s=s.replace('UDP/443 to selected Apple relay subnets rejected on forward. TCP and other destinations pass unchanged.','UDP/443 to selected Apple relay subnets rejected before/at forward. IPv6 relay TCP/443 is reset only when the FIB has no destination route; IPv4 TCP and other destinations pass unchanged.')
p.write_text(s)
p=R/'split_routes.py';s=p.read_text().replace("'transportVersion':'1.0.0'","'transportVersion':'1.0.1'");p.write_text(s)
p=R/'config/split-routing.json';d=json.loads(p.read_text());d['version']='1.0.1';d['ipv6MissingUplinkPolicy']='enrolled relay TCP/443 fast reset when FIB has no route; IPv4 fallback';p.write_text(json.dumps(d,indent=2))
p=R/'tests/test_split_routes.py';s=p.read_text();s=s.replace('assert len(rejects)==4','assert len(rejects)==6').replace("assert all('udp dport 443' in line and '@clients' in line and 'iifname \"tailscale0\"' in line for line in rejects)","assert all('@clients' in line and 'iifname \"tailscale0\"' in line for line in rejects)\n assert len([line for line in rejects if 'udp dport 443' in line])==5")
s=s.replace("assert 'tcp dport' not in text and 'policy drop' not in text","assert 'policy drop' not in text\n tcp=[line for line in rejects if 'tcp dport' in line]\n assert len(tcp)==1 and 'ip6 daddr @relay6' in tcp[0] and 'fib daddr oif missing' in tcp[0] and 'reject with tcp reset' in tcp[0]")
s+='''\n\ndef test_ipv6_reject_precedes_destination_route_lookup():
 text=render_rules(CONFIG,TS,ROUTES)
 pre=text.split('chain prerouting {',1)[1].split('}\\n',1)[0]
 assert 'hook prerouting' in pre
 assert 'udp dport 443' in pre and 'tcp dport 443 fib daddr oif missing' in pre
 assert 'ip saddr @clients4' not in pre
 assert '@clients6' in pre and '@relay6' in pre
\n\ndef test_ipv6_tcp_guard_does_not_match_tailnet_or_other_ports():
 text=render_rules(CONFIG,TS,ROUTES)
 guard=next(line for line in text.splitlines() if 'reject with tcp reset' in line)
 assert 'ip6 daddr @relay6' in guard and 'tcp dport 443' in guard
 assert '@bridge6' not in guard
''';p.write_text(s)
# Kernel dry-run only; deployment is a separate explicit step.
ts=json.loads(subprocess.check_output(['tailscale','status','--json'],text=True));cfg=json.loads((R/'clients.json').read_text())
import sys;sys.path.insert(0,str(R));from network_rules import render_rules;from split_routes import configured_routes
text=render_rules(cfg,ts,configured_routes(),True)
(D/'proposed-policy.nft').write_text(text)
x=subprocess.run(['sudo','-n','nft','--check','--file','-'],input=text,text=True,capture_output=True)
(D/'policy-check.json').write_text(json.dumps({'exit':x.returncode,'stderr':x.stderr,'backup':str(b)},indent=2));print(x.returncode)
