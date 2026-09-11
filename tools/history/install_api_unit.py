from pathlib import Path
import subprocess
root=Path('/home/jamie/cwa-weather-proxy')
unit=f'''[Unit]
Description=CWA Weather normalized data API
After=network-online.target tailscaled.service
Wants=network-online.target
[Service]
User=jamie
Group=jamie
WorkingDirectory={root}
Environment=PYTHONUNBUFFERED=1
ExecStart={root}/.venv/bin/uvicorn api:app --host 100.78.140.101 --port 18880 --no-access-log
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
UMask=0077
[Install]
WantedBy=multi-user.target
'''
Path('/etc/systemd/system/cwa-weather-api.service').write_text(unit)
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:cmd=(proc/'cmdline').read_bytes()
 except OSError:continue
 if b'python' in cmd and b'research/probe_http.py' in cmd:
  subprocess.run(['kill',proc.name],check=False)
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','cwa-weather-api'],check=True)
