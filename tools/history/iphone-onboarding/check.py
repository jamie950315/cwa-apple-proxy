"""Bounded iPhone onboarding check; records evidence separately from installation claims."""
from pathlib import Path
from datetime import datetime
import json,time,subprocess,re
ROOT=Path('/home/jamie/cwa-weather-proxy')
PHONE='100.123.14.68';PHONE6='fd7a:115c:a1e0::b01:e9a'
start=datetime.fromisoformat((ROOT/'research/iphone-onboarding/start.txt').read_text().strip()).timestamp()
def ios_rows():
    out=[]
    for line in (ROOT/'logs/bridge-reverse.jsonl').read_text().splitlines():
        try:
            r=json.loads(line)
            if r.get('time',0)>=start and re.search(r'iOS|iPhoneOS|iPadOS|iPhone',r.get('app',''),re.I):out.append(r)
        except (ValueError,TypeError):pass
    return out
end=time.monotonic()+35
while time.monotonic()<end:
    if ios_rows():break
    time.sleep(2)
clients=json.loads((ROOT/'clients.json').read_text())
rules=json.loads((ROOT/'config/managed-dns-rules.json').read_text())
ts=json.loads(subprocess.check_output(['tailscale','status','--json'],text=True))
peer=next((p for p in ts.get('Peer',{}).values() if PHONE in p.get('TailscaleIPs',[])),{})
rows=ios_rows()
report={'checkedAt':datetime.now().astimezone().isoformat(),'ipv4':PHONE,'online':peer.get('Online'),
        'enabled':any(c['ipv4']==PHONE for c in clients['enabled']),
        'ipv4IPv6DNSRuleInstalled':any(PHONE in r and PHONE6 in r and 'weatherkit.apple.com' in r for r in rules),
        'clientExitNode':'not observable from Pi5; desired None',
        'certificateInstallation':'user-reported','tlsTrust':'awaiting native HTTPS evidence',
        'nativeRequests':rows,'status':'enabled-awaiting-native-request',
        'services':{s:subprocess.run(['systemctl','is-active',s],capture_output=True,text=True).stdout.strip() for s in ['AdGuardHome','cwa-weather-api','cwa-weather-proxy','cwa-weather-routing']}}
if rows:
    report['tlsTrust']='iOS HTTPS request reached the bridge'
    report['status']='native-response-modified' if any(r.get('status')=='modified' for r in rows) else 'native-request-received-review-needed'
querylog=Path('/var/log/adguard/querylog.json')
if querylog.exists():
    with querylog.open('rb') as f:
        f.seek(max(0,querylog.stat().st_size-2_000_000));lines=f.read().decode(errors='replace').splitlines()
    dns=[]
    for line in lines:
        try:
            q=json.loads(line)
            if q.get('IP') in [PHONE,PHONE6] and any(h in str(q.get('QH','')) for h in ['weatherkit','tthr.apple','tether.edge','tether.v.aaplimg']):
                dns.append({k:q.get(k) for k in ['T','QH','QT','IP','Result']})
        except ValueError:pass
    report['recentPhoneWeatherDNS']=dns[-12:]
p=ROOT/'reports/iphone-onboarding.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='recentPhoneWeatherDNS'},ensure_ascii=False,indent=2))
