from pathlib import Path
import subprocess
root=Path('/home/jamie/cwa-weather-proxy')
Path('/etc/systemd/system/cwa-weather-routing.service').write_text(f'''[Unit]
Description=Opt-in CWA weather exit-node transport policy
After=network-online.target tailscaled.service
Wants=network-online.target
[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart={root}/.venv/bin/python {root}/network_rules.py
ExecReload={root}/.venv/bin/python {root}/network_rules.py
ExecStop={root}/.venv/bin/python {root}/network_rules.py remove
[Install]
WantedBy=multi-user.target
''')
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','cwa-weather-routing'],check=True)
