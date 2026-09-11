import json, pathlib
R=pathlib.Path('/home/jamie/cwa-weather-proxy/research')
out=[]
def add(s=''):out.append(s)
for f in ['file-F-B0046-001.json','file-O-A0038-003.json','probe-O-A0001-001.json','probe-O-A0002-001.json','probe-O-A0003-001.json','probe-C-B0024-001.json','probe-A-B0062-001.json','probe-A-B0063-001.json','probe-W-C0033-001.json','probe-W-C0033-002.json']:
 add('\n### '+f); d=json.loads((R/f).read_text())
 if f.startswith('file-F-B0046'):
  x=d['cwaopendata']['dataset'];add(json.dumps(x['datasetInfo'],ensure_ascii=False,indent=2));add('contents keys '+str(x['contents'].keys()));c=x['contents']['content'];add('content type '+type(c).__name__+' len '+str(len(c)));add('prefix '+repr(c[:400] if isinstance(c,str) else str(c)[:400]))
 elif f.startswith('file-O-A0038'):
  x=d['cwaopendata']['dataset'];add(json.dumps(x,ensure_ascii=False,indent=2)[:6000])
 elif 'O-A0001' in f or 'O-A0003' in f:
  ss=d['records']['Station'];cand=next((s for s in ss if s.get('GeoInfo',{}).get('CountyName') in ['臺北市','台北市']),ss[0]);add(cand['StationName']+' '+cand['StationId']);add(json.dumps(cand['WeatherElement'],ensure_ascii=False,indent=2)[:8000])
 elif 'O-A0002' in f:
  ss=d['records']['Station'];cand=next((s for s in ss if s.get('GeoInfo',{}).get('CountyName') in ['臺北市','台北市']),ss[0]);add(cand['StationName']+' '+cand['StationId']);add(json.dumps(cand['RainfallElement'],ensure_ascii=False,indent=2))
 elif 'C-B0024' in f:
  add(json.dumps(d['records'],ensure_ascii=False,indent=2)[:8000])
 else:add(json.dumps(d['records'],ensure_ascii=False,indent=2)[:8000])
(R/'cwa-field-inspection.txt').write_text('\n'.join(out))
print('wrote',R/'cwa-field-inspection.txt')
