from pathlib import Path
import yaml,subprocess,datetime,shutil,os
root=Path('/home/jamie/cwa-weather-proxy')
p=Path('/opt/AdGuardHome/AdGuardHome.yaml')
backup=root/'research'/'AdGuardHome.before-cwa.yaml'
# Restrict the experiment to Jamie's Mac Tailscale address.
rules=['! CWA Weather Bridge: Mac relay-block test','||tthr.apple.com^$client=100.122.163.78','||tether.edge.apple^$client=100.122.163.78']
subprocess.run(['systemctl','stop','AdGuardHome'],check=True)
try:
 if not backup.exists():shutil.copy2(p,backup);os.chmod(backup,0o600)
 text=p.read_text();data=yaml.safe_load(text)
 old=data.get('user_rules',[])
 for r in rules:
  if r not in old:old.append(r)
 data['user_rules']=old
 p.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False))
except Exception:
 if backup.exists():shutil.copy2(backup,p)
 raise
finally:subprocess.run(['systemctl','start','AdGuardHome'],check=True)
print('Mac-scoped weather relay DNS blocking enabled; backup retained.')
