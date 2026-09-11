import httpx,ssl,json,pathlib
ROOT=pathlib.Path('/home/jamie/cwa-weather-proxy');KEY=dict(x.split('=',1) for x in (ROOT/'.env').read_text().splitlines() if '=' in x)['CWA_API_KEY']
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
names=['1小時降雨機率','3小時降雨機率','6小時降雨機率','12小時降雨機率','PoP1h','PoP3h','PoP6h','PoP12h','溫度']
out=[]
with httpx.Client(verify=ctx,timeout=20,trust_env=False) as c:
 for n in names:
  r=c.get('https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-061',params={'Authorization':KEY,'format':'JSON','LocationName':'松山區','ElementName':n})
  rec={'query':n,'status':r.status_code,'bytes':len(r.content)}
  if r.status_code==200:
   try:
    d=r.json(); loc=d.get('records',{}).get('Locations',[{}])[0].get('Location',[{}])[0]; els=loc.get('WeatherElement',[]);rec['returned']=[e.get('ElementName') for e in els];rec['times']=[len(e.get('Time',[])) for e in els]
   except Exception as e:rec['error']=type(e).__name__
  else:rec['body']=r.text[:300]
  out.append(rec)
(ROOT/'research/pop-element-probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
