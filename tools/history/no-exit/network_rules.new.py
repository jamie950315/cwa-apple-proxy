"""Opt-in Weather transport: direct tailnet HTTPS and narrowly scoped relay QUIC fallback.
No client default route or Exit Node selection is changed by this service.
"""
import ipaddress,json,subprocess,sys,time,os
from pathlib import Path
from split_routes import configured_routes,approval_status
ROOT=Path(__file__).resolve().parent
TABLE='cwa_weather'

def run(args,**kw):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=30,**kw)
def remove():
    if subprocess.run(['nft','list','table','inet',TABLE],capture_output=True).returncode==0:run(['nft','delete','table','inet',TABLE])

def address_sets(config,status):
    c4=[];c6=[]
    for c in config['enabled']:
        ip=ipaddress.ip_address(c['ipv4'])
        if ip.version!=4 or ip not in ipaddress.ip_network('100.64.0.0/10'):raise ValueError('Client must have a Tailscale IPv4 address')
        c4.append(str(ip))
        for peer in status.get('Peer',{}).values():
            if str(ip) in peer.get('TailscaleIPs',[]):
                for value in peer.get('TailscaleIPs',[]):
                    x=ipaddress.ip_address(value)
                    if x.version==6 and x in ipaddress.ip_network('fd7a:115c:a1e0::/48'):c6.append(str(x))
    return sorted(set(c4)),sorted(set(c6))

def render_rules(config,status,prefixes,replace=False):
    c4,c6=address_sets(config,status)
    nets=[ipaddress.ip_network(p,strict=True) for p in prefixes]
    v4=list(ipaddress.collapse_addresses(n for n in nets if n.version==4));v6=list(ipaddress.collapse_addresses(n for n in nets if n.version==6))
    local4=[];local6=[]
    for x in status.get('Self',{}).get('TailscaleIPs',[]):
        value=ipaddress.ip_address(x);(local4 if value.version==4 else local6).append(str(value))
    if not local4:raise ValueError('Pi5 has no Tailscale IPv4')
    def nftset(name,kind,values):
        return 'set '+name+' { type '+kind+'; flags interval; '+('elements = { '+', '.join(map(str,values))+' }; ' if values else '')+'}\n'
    text=('delete table inet '+TABLE+'\n' if replace else '')+'table inet '+TABLE+' {\n'
    for name,kind,items in [('relay4','ipv4_addr',v4),('relay6','ipv6_addr',v6),('clients4','ipv4_addr',c4),('clients6','ipv6_addr',c6),('bridge4','ipv4_addr',local4),('bridge6','ipv6_addr',local6)]:text+=nftset(name,kind,items)
    text+='chain input { type filter hook input priority -10; policy accept;\n'
    text+='iifname "tailscale0" ip saddr @clients4 ip daddr @bridge4 udp dport 443 counter reject with icmpx type port-unreachable comment "cwa direct tailnet QUIC fallback"\n'
    text+='iifname "tailscale0" ip6 saddr @clients6 ip6 daddr @bridge6 udp dport 443 counter reject with icmpx type port-unreachable comment "cwa direct tailnet QUIC fallback"\n}\n'
    text+='chain forward { type filter hook forward priority -10; policy accept;\n'
    text+='iifname "tailscale0" ip saddr @clients4 ip daddr @relay4 udp dport 443 counter reject with icmpx type port-unreachable comment "cwa selective relay QUIC fallback"\n'
    text+='iifname "tailscale0" ip6 saddr @clients6 ip6 daddr @relay6 udp dport 443 counter reject with icmpx type port-unreachable comment "cwa selective relay QUIC fallback"\n}\n}\n'
    return text

def apply():
    status=json.loads(run(['tailscale','status','--json']).stdout);config=json.loads((ROOT/'clients.json').read_text());prefixes=configured_routes()
    replace=subprocess.run(['nft','list','table','inet',TABLE],capture_output=True).returncode==0
    text=render_rules(config,status,prefixes,replace)
    run(['nft','--check','--file','-'],input=text);run(['nft','--file','-'],input=text)
    c4,c6=address_sets(config,status);approval=approval_status(prefixes,status.get('Self',{}))
    result={'transportVersion':'1.0.0','time':int(time.time()),'mode':'split-dns-relay-routes','clients4':c4,'clients6':c6,
            'relayPrefixes':prefixes,'relayRouteApproval':approval,'requiredClientExitNode':'None',
            'policy':'Enrolled clients: UDP/443 to Pi5 rejected on input; UDP/443 to selected Apple relay subnets rejected on forward. TCP and other destinations pass unchanged.',
            'relayRoutingReady':not approval['pending']}
    path=ROOT/'data/routing-status.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2));os.chmod(tmp,0o644);tmp.replace(path)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':remove() if len(sys.argv)>1 and sys.argv[1]=='remove' else apply()
