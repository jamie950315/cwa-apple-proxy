from pathlib import Path
import json,shutil,time,subprocess
R=Path('/home/jamie/cwa-weather-proxy');D=R/'research/approved-split';V=json.loads((D/'mac-verified-final.json').read_text());start=V['coldStartAt']
rows=[]
for line in (R/'logs/bridge-reverse.jsonl').read_text().splitlines():
 try:
  x=json.loads(line)
  if x.get('time',0)>=start and x.get('status')=='modified' and 'macOS' in x.get('app',''):rows.append(x)
 except ValueError:pass
P=R/'reports/approved-split-native';P.mkdir(exist_ok=True);paths=[]
for e in rows:
 src=R/e['proof']
 if not src.exists():continue
 dest=P/src.name
 shutil.copytree(src,dest,dirs_exist_ok=True);paths.append(str(dest))
(D/'native-proof-list.json').write_text(json.dumps(paths))
summary={'time':time.time(),'coldStartAt':start,'rows':rows,'appResponses':sum('Weather_macOS' in x.get('app','') for x in rows),'widgetResponses':sum('WeatherWidget_macOS' in x.get('app','') for x in rows),'preservedProofCount':len(paths)}
(D/'native-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
p=subprocess.run(['node','research/approved-split/audit_native.mjs'],cwd=R,capture_output=True,text=True)
(D/'native-audit.log').write_text(p.stdout+p.stderr);print(json.dumps({**{k:v for k,v in summary.items() if k!='rows'},'auditExit':p.returncode}))
