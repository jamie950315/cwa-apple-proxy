import httpx,ssl,json,pathlib
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
r=httpx.get('https://opendata.cwa.gov.tw/apidoc/v1',verify=ctx,timeout=20,trust_env=False)
print(r.status_code,len(r.content),r.headers.get('content-type'))
d=r.json();pathlib.Path('/home/jamie/cwa-weather-proxy/research/openapi.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
out=[]
for p in ['/v1/rest/datastore/C-B0024-001','/v1/rest/datastore/O-A0002-001','/v1/rest/datastore/F-D0047-061','/v1/rest/datastore/A-B0062-001','/v1/rest/datastore/A-B0063-001']:
 out.append('\n'+p)
 for x in d.get('paths',{}).get(p,{}).get('get',{}).get('parameters',[]):out.append(' | '.join(str(x.get(k,'')) for k in ['name','in','type','description']))
pathlib.Path('/home/jamie/cwa-weather-proxy/research/openapi-params.txt').write_text('\n'.join(out))
print('\n'.join(out))
