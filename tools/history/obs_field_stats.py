import json,pathlib,collections
R=pathlib.Path('/home/jamie/cwa-weather-proxy/research')
d=json.loads((R/'probe-O-A0003-001.json').read_text())
vals=collections.defaultdict(list)
for s in d['records']['Station']:
 w=s.get('WeatherElement',{})
 for k in ['VisibilityDescription','SunshineDuration','AirPressure','UVIndex']:
  v=w.get(k)
  if v not in [None,'','-99','-999'] and len(vals[k])<20:vals[k].append((s.get('StationName'),v,s.get('GeoInfo',{}).get('StationAltitude')))
print(json.dumps(vals,ensure_ascii=False,indent=2))
