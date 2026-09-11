from pathlib import Path
import yaml,subprocess,shutil,os,json
root=Path('/home/jamie/cwa-weather-proxy');p=Path('/opt/AdGuardHome/AdGuardHome.yaml')
client='100.122.163.78'
rules=[
 '! CWA Weather Bridge: Mac-only TLS DNS routing',
 f'||weatherkit.apple.com^$dnsrewrite=NOERROR;A;100.78.140.101,client={client}',
 f'||weatherkit.apple.com^$dnsrewrite=NOERROR;;,dnstype=AAAA,client={client}',
 f'||weatherkit.apple.com^$dnsrewrite=NOERROR;;,dnstype=HTTPS,client={client}',
 f'||tthr.apple.com^$client={client}',
 f'||tether.edge.apple^$client={client}',
]
# Redirect only this consenting Mac's incoming TCP/443. All other SNI goes back to tailscaled.
rule=['-i','tailscale0','-s',client,'-d','100.78.140.101','-p','tcp','--dport','443','-m','comment','--comment','cwa-weather-mac','-j','REDIRECT','--to-ports','19443']
if subprocess.run(['iptables','-t','nat','-C','PREROUTING',*rule],stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['iptables','-t','nat','-I','PREROUTING','1',*rule],check=True)
subprocess.run(['systemctl','stop','AdGuardHome'],check=True)
try:
 backup=root/'research/AdGuardHome.before-cwa.yaml'
 if not backup.exists():shutil.copy2(p,backup);os.chmod(backup,0o600)
 d=yaml.safe_load(p.read_text());old=d.get('user_rules',[])
 for r in rules:
  if r not in old:old.append(r)
 d['user_rules']=old
 p.write_text(yaml.safe_dump(d,allow_unicode=True,sort_keys=False))
finally:subprocess.run(['systemctl','start','AdGuardHome'],check=True)
print(json.dumps({'client':client,'weatherkitDNS':'100.78.140.101','routerPort':19443}))
