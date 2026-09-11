from pathlib import Path
import subprocess
root=Path('/home/jamie/cwa-weather-proxy')
units={
'cwa-weather-sni':f'''[Unit]
Description=CWA Weather TLS SNI router
After=network-online.target tailscaled.service
Wants=network-online.target
[Service]
User=jamie
Group=jamie
WorkingDirectory={root}
ExecStart={root}/.venv/bin/python {root}/sni_router.py
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
UMask=0077
[Install]
WantedBy=multi-user.target
''',
'cwa-weather-proxy':f'''[Unit]
Description=CWA Apple Weather reverse proxy
After=network-online.target
Wants=network-online.target
[Service]
User=jamie
Group=jamie
WorkingDirectory={root}
Environment=PYTHONUNBUFFERED=1
ExecStart={root}/.venv/bin/mitmdump --mode reverse:https://weatherkit.apple.com --listen-host 127.0.0.1 --listen-port 18443 --set keep_host_header=true --set confdir={root}/certs/mitm --certs weatherkit.apple.com={root}/certs/weatherkit.pem --set flow_detail=0 --set termlog_verbosity=warn -s {root}/research/probe.py
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
UMask=0077
[Install]
WantedBy=multi-user.target
'''}
for name,text in units.items():Path('/etc/systemd/system/'+name+'.service').write_text(text)
for f in ['sni-router.pid','reverse-probe.pid']:
    p=root/'research'/f
    if p.exists():subprocess.run(['kill',p.read_text().strip()],check=False)
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now',*[name+'.service' for name in units]],check=True)
