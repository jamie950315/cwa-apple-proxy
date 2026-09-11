import json,pathlib
base=pathlib.Path('/home/jamie/cwa-weather-proxy')
with (base/'research'/'cwa-schema.txt').open('w') as out:
 def emit(*a):print(*a,file=out)
 for p in (base/'data').glob('*.json'):
  d=json.loads(p.read_text());r=d.get('records',{});emit('\nDATASET',p.name,'success',d.get('success'),'keys',list(r))
  if 'Station' in r:emit('count',len(r['Station']));emit(json.dumps(r['Station'][0],ensure_ascii=False,indent=2))
  for k in ['Locations','locations']:
   if k in r:
    g=r[k][0];emit('group keys',list(g));ls=g.get('Location',g.get('location',[]));emit('locations',len(ls));loc=ls[0];emit('location',json.dumps({a:b for a,b in loc.items() if a not in ['WeatherElement','weatherElement']},ensure_ascii=False))
    for el in loc.get('WeatherElement',loc.get('weatherElement',[])):emit(json.dumps({a:(b[:2] if isinstance(b,list) else b) for a,b in el.items()},ensure_ascii=False))
