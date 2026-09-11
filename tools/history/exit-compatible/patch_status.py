"""Update diagnostic wording for optional Exit Nodes; transport rule bodies stay intact."""
from pathlib import Path
import json,time,shutil,hashlib
ROOT=Path('/home/jamie/cwa-weather-proxy');OUT=ROOT/'research/exit-compatible'
for name in ['split_routes.py','network_rules.py','api.py']:
    p=ROOT/name;backup=OUT/(name+'.pre-102')
    if not backup.exists():shutil.copy2(p,backup)
p=ROOT/'split_routes.py';s=p.read_text()
s=s.replace('Client Exit Node stays None.','Client Exit Node is optional when restricted DNS is exit-compatible.')
s=s.replace("'transportVersion':'1.0.1'","'transportVersion':'1.0.2'")
s=s.replace("'requiredClientExitNode':'None'","'requiredClientExitNode':None,'exitNodeSelection':'optional'")
s=s.replace("'scope':'Weather DNS maps directly to Pi5; additional relay destination subnets use Pi5. General default route stays unchanged.'", "'scope':'Weather and selected relay subnets use Pi5; ordinary traffic uses the client-selected exit node, or its original default route when no exit is selected.'")
s=s.replace("'restrictedDNS':dns,", "'restrictedDNS':dns,'exitCompatibleDNS':exit_dns_evidence(),")
anchor='def status():\n'
helper='''def exit_dns_evidence():
    # These UI flags are last-verified evidence. The server CLI does not expose them live.
    try:
        data=json.loads((ROOT/'config/exit-dns-compatibility.json').read_text())
        rows=data.get('domains',{})
        complete=all(rows.get(d,{}).get('nameserver')=='100.78.140.101' and rows.get(d,{}).get('useWithExitNode') is True for d in DNS_DOMAINS)
        return {'lastVerifiedAt':data.get('verifiedAt'),'allFourEnabledAtVerification':complete,'liveFlagMonitoring':False,'evidence':'Tailscale Admin Console saved configuration; client exit-switch testing recorded separately'}
    except (OSError,ValueError,TypeError,AttributeError):
        return {'allFourEnabledAtVerification':False,'liveFlagMonitoring':False,'evidence':'no valid saved verification'}

'''
if 'def exit_dns_evidence()' not in s:
    if anchor not in s:raise RuntimeError('split status anchor absent')
    s=s.replace(anchor,helper+anchor)
p.write_text(s)
p=ROOT/'network_rules.py';s=p.read_text();s=s.replace("'transportVersion':'1.0.1'","'transportVersion':'1.0.2'").replace("'requiredClientExitNode':'None'","'requiredClientExitNode':None,'exitNodeSelection':'optional'");p.write_text(s)
p=ROOT/'api.py';s=p.read_text();needle="result['splitRoutes']=read_json(ROOT/'data/split-route-status.json',{})"
if needle not in s:raise RuntimeError('API status anchor absent')
new="result['exitCompatibility']=read_json(ROOT/'data/exit-compatibility-status.json',{})"
if new not in s:s=s.replace(needle,needle+'\n    '+new)
p.write_text(s)
config={'verifiedAt':int(time.time()),'source':'Tailscale Admin Console; four saved rows visually verified after updates','domains':{d:{'nameserver':'100.78.140.101','useWithExitNode':True} for d in ['weatherkit.apple.com','tthr.apple.com','tether.edge.apple','tether.v.aaplimg.com']},'globalDNS':'unchanged','existingSubnetRoutes':'unchanged'}
(ROOT/'config/exit-dns-compatibility.json').write_text(json.dumps(config,ensure_ascii=False,indent=2))
# Assert the firewall render function is byte-for-byte identical to the baseline.
old=(OUT/'network_rules.py.pre-102').read_text();new=(ROOT/'network_rules.py').read_text()
extract=lambda t:t.split('def render_rules(',1)[1].split('\ndef apply():',1)[0]
assert extract(old)==extract(new),'Transport firewall function unexpectedly changed'
print('1.0.2 status patch staged; firewall rule rendering unchanged')
