"""Manage narrowly scoped Apple relay subnet advertisements. Client Exit Node is optional when restricted DNS is exit-compatible.
Route approval is a separate Tailscale control-plane action; never infer it from /0.
"""
from pathlib import Path
import argparse,ipaddress,json,os,subprocess,time
ROOT=Path(__file__).resolve().parent
STATE=ROOT/'config/split-route-state.json'
CONFIG=ROOT/'config/split-routing.json'

def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True,timeout=25).stdout

def configured_routes():
    routes=json.loads(CONFIG.read_text())['relayPrefixes']
    allowed=[ipaddress.ip_network(p) for group in json.loads((ROOT/'config/apple-prefixes.json').read_text()).values() for p in group]
    for route in routes:
        n=ipaddress.ip_network(route,strict=True)
        if n.prefixlen<(16 if n.version==4 else 40):raise ValueError('Relay prefix is too broad')
        if not any(a.version==n.version and n.subnet_of(a) for a in allowed):raise ValueError('Relay route is outside verified Apple prefixes')
    return list(dict.fromkeys(routes))

def specific(routes):
    return [str(ipaddress.ip_network(p)) for p in routes if ipaddress.ip_network(p).prefixlen>0]

def merge_routes(current,desired,remove=()):
    # --advertise-routes edits only non-default advertisements; it preserves the exit advertisement flag.
    return list(dict.fromkeys([p for p in specific(current) if p not in remove]+desired))

def approval_status(desired,self_node):
    approved=set(specific(self_node.get('AllowedIPs') or [])+specific(self_node.get('PrimaryRoutes') or []))
    return {'approved':[p for p in desired if p in approved],
            'pending':[p for p in desired if p not in approved]}

DNS_DOMAINS=['weatherkit.apple.com','tthr.apple.com','tether.edge.apple','tether.v.aaplimg.com']
def restricted_dns_status(text):
    found={}
    for line in text.splitlines():
        if ' -> ' not in line:continue
        left,right=line.strip().removeprefix('- ').split(' -> ',1)
        domain=left.strip().rstrip('.')
        if domain in DNS_DOMAINS:
            found.setdefault(domain,[]).append(right.strip())
    return {'domains':found,'requiredDomains':DNS_DOMAINS,
            'ready':all(found.get(d)==['100.78.140.101'] for d in DNS_DOMAINS)}

def exit_dns_evidence():
    # These UI flags are last-verified evidence. The server CLI does not expose them live.
    try:
        data=json.loads((ROOT/'config/exit-dns-compatibility.json').read_text())
        rows=data.get('domains',{})
        complete=all(rows.get(d,{}).get('nameserver')=='100.78.140.101' and rows.get(d,{}).get('useWithExitNode') is True for d in DNS_DOMAINS)
        return {'lastVerifiedAt':data.get('verifiedAt'),'allFourEnabledAtVerification':complete,'liveFlagMonitoring':False,'evidence':'Tailscale Admin Console saved configuration; client exit-switch testing recorded separately'}
    except (OSError,ValueError,TypeError,AttributeError):
        return {'allFourEnabledAtVerification':False,'liveFlagMonitoring':False,'evidence':'no valid saved verification'}

def status():
    desired=configured_routes();prefs=json.loads(run(['tailscale','debug','prefs']))
    ts=json.loads(run(['tailscale','status','--json']));a=approval_status(desired,ts.get('Self',{}))
    advertised=prefs.get('AdvertiseRoutes') or []
    try:dns=restricted_dns_status(run(['tailscale','dns','status']))
    except (subprocess.SubprocessError,ValueError):dns={'ready':False,'error':'DNS status unavailable'}
    ipv6_probe=subprocess.run(['ip','-6','route','get','2403:300:a04:2000::61'],capture_output=True,text=True,timeout=5)
    ipv6_uplink=ipv6_probe.returncode==0 and 'unreachable' not in ipv6_probe.stdout and 'tailscale0' not in ipv6_probe.stdout
    result={'transportVersion':'1.0.2','mode':'split-dns-relay-routes','time':int(time.time()),
            'requiredClientExitNode':None,'exitNodeSelection':'optional','requestedRoutes':desired,'advertisedRoutes':advertised,
            'restrictedDNS':dns,'exitCompatibleDNS':exit_dns_evidence(),'ipv6UplinkAvailable':ipv6_uplink,'ipv6MissingUplinkBehavior':'Enrolled relay UDP rejected early; relay TCP reset only when the destination FIB route is missing. IPv4 TCP remains usable.',
            'configurationReady':not a['pending'] and all(p in advertised for p in desired) and dns['ready'],
            'missingAdvertisements':[p for p in desired if p not in advertised],**a,
            'relayRoutingReady':not a['pending'] and all(p in advertised for p in desired),
            'approvalMeaning':'exact approved subnet routes; default /0 exit-node advertisements are excluded',
            'scope':'Weather and selected relay subnets use Pi5; ordinary traffic uses the client-selected exit node, or its original default route when no exit is selected.',
            'approvalInstructions':'Tailscale Admin Console > Machines > Pi5 > Edit route settings > approve the four relay subnet routes.'}
    return result

def save(data):
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));os.chmod(tmp,0o644);tmp.replace(STATE)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['status','apply','withdraw'])
    parser.add_argument('--write-status',action='store_true')
    args=parser.parse_args()
    if args.action=='status':
        result=status()
        if args.write_status:
            path=ROOT/'data/split-route-status.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2));tmp.replace(path)
        print(json.dumps(result,ensure_ascii=False,indent=2));return
    if os.geteuid()!=0:parser.error('Use sudo for route changes')
    current=json.loads(run(['tailscale','debug','prefs'])).get('AdvertiseRoutes') or []
    if args.action=='apply':
        wanted=configured_routes()
        if STATE.exists():state=json.loads(STATE.read_text())
        else:
            original=current
            pilot=ROOT/'research/no-exit/advertise-before.json'
            if pilot.exists():original=json.loads(pilot.read_text())['routes']
            state={'createdAt':int(time.time()),'originalAdvertisements':original,'ownedRoutes':[p for p in wanted if p not in original]}
        # Remove only this task's unapproved single-host probe.
        remove=['17.253.87.61/32'] if '17.253.87.61/32' not in state['originalAdvertisements'] else []
        merged=merge_routes(current,wanted,remove)
        run(['tailscale','set','--advertise-routes='+','.join(merged)])
        state.update(requestedRoutes=wanted,appliedAt=int(time.time()));save(state)
    else:
        if not STATE.exists():parser.error('No owned-route state; nothing to withdraw')
        state=json.loads(STATE.read_text())
        merged=merge_routes(current,[],state.get('ownedRoutes',[]))
        run(['tailscale','set','--advertise-routes='+','.join(merged)])
        state['withdrawnAt']=int(time.time());save(state)
    print(json.dumps(status(),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
