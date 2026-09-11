import subprocess,json,time
from pathlib import Path
root=Path('/home/jamie/cwa-weather-proxy')
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout
for name in ['cwa-weather-sni','cwa-weather-proxy']:run('systemctl','is-active',name)
try:
    run('tailscale','serve','--https=443','off')
    run('tailscale','serve','--bg','--tcp=443','tcp://127.0.0.1:19443')
    result=run('curl','--resolve','pi5.tail19030f.ts.net:443:100.78.140.101','--max-time','15','--silent','--show-error','--output','/dev/null','--write-out','%{http_code}','https://pi5.tail19030f.ts.net/')
    if result!='200':raise RuntimeError('Existing service health '+result)
    print('Serve TLS passthrough activated; original URL HTTP 200')
except Exception:
    subprocess.run(['tailscale','serve','--tcp=443','off'],check=False)
    run('tailscale','serve','--bg','--https=443','http://127.0.0.1:8017')
    run('tailscale','serve','--bg','--https=443','--set-path=/runpod-image-editor','http://127.0.0.1:8789')
    raise
finally:
    rule=['-i','tailscale0','-s','100.122.163.78','-d','100.78.140.101','-p','tcp','--dport','443','-m','comment','--comment','cwa-weather-mac','-j','REDIRECT','--to-ports','19443']
    subprocess.run(['iptables','-t','nat','-D','PREROUTING',*rule],check=False)
(root/'research'/'tailscale-serve-active.json').write_text(run('tailscale','serve','status','--json'))
