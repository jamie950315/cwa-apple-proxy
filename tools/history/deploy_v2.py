from pathlib import Path
import subprocess,time,json,os
ROOT=Path('/home/jamie/cwa-weather-proxy')
def run(args,timeout=45):
 r=subprocess.run(args,cwd=ROOT,check=True,capture_output=True,text=True,timeout=timeout)
 print(r.stdout.strip(),flush=True);return r.stdout
# Preserve source and system-unit backups from before changes.
p=ROOT/'network_rules.py';s=p.read_text().replace("ROOT/'research/apple-prefixes.json'","ROOT/'config/apple-prefixes.json'")
s=s.replace("return 'set '+name+' { type '+kind+'; flags interval; elements = { '+', '.join(map(str,elements))+' }; }\\n'", "return 'set '+name+' { type '+kind+'; flags interval; '+('elements = { '+', '.join(map(str,elements))+' }; ' if elements else '')+'}\\n'")
p.write_text(s)
run(['sudo','-u','jamie',str(ROOT/'.venv/bin/python'),'-m','pytest','-q'])
run(['/home/linuxbrew/.linuxbrew/bin/node','--test','tests/mapper.test.mjs'])
run([str(ROOT/'.venv/bin/python'),'-m','compileall','-q','api.py','addon.py','cwa_client.py','cwa_model.py','cwa_snapshot.py','bridgectl.py','network_rules.py'])
unit=Path('/etc/systemd/system/cwa-weather-forward.service')
unit.write_text(f'''[Unit]
Description=CWA Weather domain-scoped explicit proxy
After=network-online.target tailscaled.service cwa-weather-api.service cwa-weather-codec.service
Wants=network-online.target
[Service]
User=jamie
Group=jamie
WorkingDirectory={ROOT}
Environment=PYTHONUNBUFFERED=1
ExecStart={ROOT}/.venv/bin/mitmdump --listen-host 100.78.140.101 --listen-port 18940 --set confdir={ROOT}/certs/mitm --certs weatherkit.apple.com={ROOT}/certs/weatherkit.pem --allow-hosts ^weatherkit\\.apple\\.com:443$ --set flow_detail=0 --set termlog_verbosity=warn -s {ROOT}/addon.py
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
UMask=0077
[Install]
WantedBy=multi-user.target
''')
# Replace the old research proxy on the same port with the translating production service.
ps=subprocess.check_output(['ps','-eo','pid,args'],text=True)
for line in ps.splitlines():
 if 'mitmdump --listen-host 100.78.140.101 --listen-port 18940' in line and '-s research/probe.py' in line:
  os.kill(int(line.split()[0]),15)
run(['systemctl','daemon-reload'])
run(['systemctl','restart','cwa-weather-codec','cwa-weather-api'])
time.sleep(1)
run(['curl','-fsS','--max-time','25','http://100.78.140.101:18880/v1/cwa/weather?latitude=25.09&longitude=121.56'])
run(['systemctl','restart','cwa-weather-proxy'])
run(['systemctl','enable','--now','cwa-weather-forward'])
# Restore the pre-existing Runpod path in the HTTPS fallback backend.
run(['tailscale','serve','--bg','--https=18444','--set-path=/runpod-image-editor','http://127.0.0.1:8789'])
run([str(ROOT/'.venv/bin/python'),'bridgectl.py','apply'])
run(['systemctl','is-active','cwa-weather-api','cwa-weather-codec','cwa-weather-proxy','cwa-weather-forward','cwa-weather-sni','cwa-weather-routing'])
run(['curl','-fsS','--max-time','10','http://100.78.140.101:18880/healthz'])
(ROOT/'data/deployment-v2.json').write_text(json.dumps({'version':'0.2.0','deployedAt':int(time.time()),'stage':'backend deployed; native verification pending'}))
