from pathlib import Path
import subprocess
root=Path('/home/jamie/cwa-weather-proxy');node=(root/'research/node-path.txt').read_text().strip()
if not Path(node).is_file():raise RuntimeError('Node executable missing')
unit=f'''[Unit]
Description=CWA Apple Weather FlatBuffers scalar mapper
After=network-online.target
[Service]
User=jamie
Group=jamie
WorkingDirectory={root}
ExecStart={node} {root}/codec_server.mjs
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
UMask=0077
[Install]
WantedBy=multi-user.target
'''
Path('/etc/systemd/system/cwa-weather-codec.service').write_text(unit)
p=Path('/etc/systemd/system/cwa-weather-proxy.service')
s=p.read_text().replace(str(root/'research/probe.py'),str(root/'addon.py'))
s=s.replace('After=network-online.target','After=network-online.target cwa-weather-api.service cwa-weather-codec.service')
p.write_text(s)
subprocess.run(['systemctl','daemon-reload'],check=True)
subprocess.run(['systemctl','enable','--now','cwa-weather-codec'],check=True)
subprocess.run(['systemctl','restart','cwa-weather-proxy'],check=True)
print('Mapper active')
