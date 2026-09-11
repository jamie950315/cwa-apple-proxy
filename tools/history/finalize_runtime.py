from pathlib import Path
import subprocess,json,time
ROOT=Path('/home/jamie/cwa-weather-proxy')
p=ROOT/'addon.py';s=p.read_text().replace('import asyncio,base64,','import os,asyncio,base64,')
s=s.replace("VERSION='0.2.0'", "VERSION='0.2.0'\nMODE=os.getenv('CWA_PROXY_MODE','reverse')")
s=s.replace("ROOT/'logs/bridge.jsonl'", "ROOT/'logs'/f'bridge-{MODE}.jsonl'")
s=s.replace("temp.replace(ROOT/'data/bridge-status.json')", "temp.replace(ROOT/'data'/('bridge-status-forward.json' if MODE=='forward' else 'bridge-status.json'))")
s=s.replace("event={'version':VERSION,", "event={'mode':MODE,'version':VERSION,")
s=s.replace("'application/vnd.apple.flatbuffer' not in flow.response.headers.get('content-type','')", "not re.search(r'application/vnd\\.apple\\.flatbuffer\\s*;\\s*messageType=\\\"?WK2\\.Weather(?:[\\\";\\s]|$)',flow.response.headers.get('content-type',''),re.I)")
p.write_text(s)
p=ROOT/'api.py';s=p.read_text().replace("result['routing']=", "result['forwardBridge']=read_json(ROOT/'data/bridge-status-forward.json',{})\n    result['routing']=");p.write_text(s)
p=Path('/etc/systemd/system/cwa-weather-forward.service');s=p.read_text().replace('Environment=PYTHONUNBUFFERED=1','Environment=PYTHONUNBUFFERED=1\nEnvironment=CWA_PROXY_MODE=forward');p.write_text(s)
# Tests run before restarting modified daemons.
r=subprocess.run(['sudo','-u','jamie',str(ROOT/'.venv/bin/python'),'-m','pytest','-q'],cwd=ROOT,capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode()
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','restart','cwa-weather-api','cwa-weather-proxy','cwa-weather-forward'],check=True)
subprocess.run(['systemctl','is-active','cwa-weather-api','cwa-weather-codec','cwa-weather-proxy','cwa-weather-forward','cwa-weather-sni','cwa-weather-routing'],check=True)
(ROOT/'data/deployment-v2.json').write_text(json.dumps({'version':'0.2.0','deployedAt':int(time.time()),'stage':'deployed; macOS native responses verified; iOS certificate onboarding pending'}))
print('Release runtime finalized')
