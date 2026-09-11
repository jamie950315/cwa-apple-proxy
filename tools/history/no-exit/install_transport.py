from pathlib import Path
from datetime import datetime
import shutil,json,subprocess,os
ROOT=Path('/home/jamie/cwa-weather-proxy')
backup=ROOT/'backups'/('no-exit-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
for name in ['network_rules.py','bridgectl.py','api.py','dashboard.html','README.md','clients.json','config/managed-dns-rules.json']:
 p=ROOT/name
 if p.exists():
  dst=backup/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
( ROOT/'research/no-exit/transport-backup.txt').write_text(str(backup))
shutil.copy2(ROOT/'research/no-exit/network_rules.new.py',ROOT/'network_rules.py')
p=ROOT/'bridgectl.py';s=p.read_text()
a="f'||tthr.apple.com^$client={selector}',f'||tether.edge.apple^$client={selector}'])"
b="f'||tthr.apple.com^$client={selector}',f'||tether.edge.apple^$client={selector}',\n          f'||tether.v.aaplimg.com^$client={selector}'])"
if a not in s:raise RuntimeError('Unexpected bridgectl source; preserving backup')
p.write_text(s.replace(a,b))
p=ROOT/'split_routes.py';s=p.read_text();s=s.replace("args=parser.parse_args()", "parser.add_argument('--write-status',action='store_true')\n    args=parser.parse_args()")
a="if args.action=='status':print(json.dumps(status(),ensure_ascii=False,indent=2));return"
b="""if args.action=='status':
        result=status()
        if args.write_status:
            path=ROOT/'data/split-route-status.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2));tmp.replace(path)
        print(json.dumps(result,ensure_ascii=False,indent=2));return"""
if a not in s:raise RuntimeError('Unexpected route status source')
p.write_text(s.replace(a,b))
p=ROOT/'api.py';s=p.read_text();a="result['routing']=read_json(ROOT/'data/routing-status.json',{})"
if a not in s:raise RuntimeError('Unexpected status source')
s=s.replace(a,a+"\n    result['splitRoutes']=read_json(ROOT/'data/split-route-status.json',{})")
p.write_text(s)
print(json.dumps({'backup':str(backup),'staged':True}))
