"""Probe approval of one relay host route while preserving the existing LAN and exit-node advertisement."""
from pathlib import Path
import subprocess,json,time,ipaddress
ROOT=Path(__file__).resolve().parent
p=json.loads(subprocess.check_output(['tailscale','debug','prefs'],text=True))
old=p.get('AdvertiseRoutes') or []
backup=ROOT/'advertise-before.json'
if not backup.exists():backup.write_text(json.dumps({'routes':old,'time':time.time()},indent=2))
nondefaults=[x for x in old if ipaddress.ip_network(x).prefixlen>0]
route='17.253.87.61/32'
new=list(dict.fromkeys(nondefaults+[route]))
r=subprocess.run(['sudo','tailscale','set','--advertise-routes='+','.join(new)],text=True,capture_output=True,timeout=20)
time.sleep(5)
s=json.loads(subprocess.check_output(['tailscale','status','--json'],text=True))
result={'before':old,'added':route,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'self':{k:s.get('Self',{}).get(k) for k in ['ID','PrimaryRoutes','AllowedIPs']}}
(ROOT/'route-probe.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
