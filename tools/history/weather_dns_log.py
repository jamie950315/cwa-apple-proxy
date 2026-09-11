from pathlib import Path
import json
p=Path('/var/log/adguard/querylog.json')
with p.open('rb') as f:
 f.seek(max(0,p.stat().st_size-3000000)); lines=f.read().decode(errors='replace').splitlines()
out=[]
for line in lines:
 try:
  d=json.loads(line)
  q=str(d.get('QH','')).lower()
  if any(x in q for x in ['tthr','tether','weatherkit','weather-data','weather-edge']):
   out.append({k:v for k,v in d.items() if k in ['T','QH','QT','IP','Result','Upstream','Elapsed','Reason','Rules']})
 except Exception:pass
Path('/home/jamie/cwa-weather-proxy/research/weather-dns-log.json').write_text(json.dumps(out[-50:],ensure_ascii=False,indent=2))
