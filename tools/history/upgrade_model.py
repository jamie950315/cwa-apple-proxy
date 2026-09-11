from pathlib import Path
import json
root=Path('/home/jamie/cwa-weather-proxy')
p=root/'cwa_model.py';s=p.read_text()
s=s.replace('    try:\n        n = float(value)','    try:\n        if isinstance(value, bool): return None\n        n = float(value)',1)
s=s.replace("return int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp())", "dt = datetime.fromisoformat(value.replace('Z', '+00:00'))\n        if dt.tzinfo is None: dt = dt.replace(tzinfo=TZ)\n        return int(dt.timestamp())")
s=s.replace(".replace('風','')", ".replace('風','').replace('偏','').strip()")
p.write_text(s)
regions=json.loads((root/'cwa_regions.json').read_text());towns=[]
for county,n in regions.items():
 d=json.loads((root/'data'/f'F-D0047-{n:03d}.json').read_text())
 for group in d['records']['Locations']:
  for l in group['Location']:
   towns.append({'county':county,'town':l['LocationName'],'geocode':l.get('Geocode'),'latitude':float(l['Latitude']),'longitude':float(l['Longitude']),'dataset':n})
(root/'town_index.json').write_text(json.dumps(towns,ensure_ascii=False,indent=2))
print('Model upgraded; forecast reference points:',len(towns))
