from pathlib import Path
import subprocess,json
ROOT=Path('/home/jamie/cwa-weather-proxy/research/no-exit')
cmd=r'''python3 - <<'PY'
import subprocess,json,os
T='/Applications/Tailscale.app/Contents/MacOS/Tailscale'
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=25);return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
r={'prefs':{},'time':run(['date','-Iseconds']),'sudo':run(['sudo','-n','true'])}
p=run([T,'debug','prefs'])
try:
 d=json.loads(p['stdout']);r['prefs']={k:d.get(k) for k in ['RouteAll','CorpDNS','ExitNodeID','ExitNodeIP','ExitNodeAllowLANAccess']}
except Exception:r['prefsError']=p
for key,command in [('dns',['scutil','--dns']),('proxy',['scutil','--proxy']),('routeDefault',['route','-n','get','1.1.1.1']),('piRoute',['route','-n','get','100.78.140.101']),('app',['pgrep','-fl','Weather|weatherd']),('wifiDNS',['networksetup','-getdnsservers','Wi-Fi']),('egress',['curl','-sS','--max-time','10','https://www.cloudflare.com/cdn-cgi/trace'])]:r[key]=run(command)
print(json.dumps(r,ensure_ascii=False,indent=2))
PY'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','jamie@100.122.163.78',cmd],capture_output=True,text=True,timeout=90)
(ROOT/'baseline-mac.json').write_text(p.stdout)
(ROOT/'baseline-mac.stderr').write_text(p.stderr)
print('ssh exit',p.returncode)
