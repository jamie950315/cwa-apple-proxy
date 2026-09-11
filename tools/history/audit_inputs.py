from pathlib import Path
import json,time
p=Path('/home/jamie/cwa-weather-proxy')
d=json.loads((p/'data/F-D0047-061.json').read_text());loc=d['records']['Locations'][0]['Location'][0]
w=json.loads((p/'data/F-D0047-063.json').read_text());wl=w['records']['Locations'][0]['Location'][0]
out={}
for key,l in [('short',loc),('weekly',wl)]:
 out[key]={'town':l['LocationName'],'elements':[{**e,'Time':e['Time'][:2]} for e in l['WeatherElement']]}
texts=set();codes={}
for f in (p/'data').glob('F-D0047-*.json'):
 d=json.loads(f.read_text())
 for g in d.get('records',{}).get('Locations',[]):
  for l in g.get('Location',[]):
   for e in l['WeatherElement']:
    for t in e.get('Time',[]):
     for v in t.get('ElementValue',[]):
      if v.get('WeatherCode'):codes[v['WeatherCode']]=v.get('Weather')
out['conditions']=codes
(p/'research/audit-inputs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
