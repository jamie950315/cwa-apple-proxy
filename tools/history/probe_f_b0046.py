import httpx,ssl,json,pathlib
root=pathlib.Path('/home/jamie/cwa-weather-proxy');key=dict(x.split('=',1) for x in (root/'.env').read_text().splitlines() if '=' in x)['CWA_API_KEY']
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
out=[]
with httpx.Client(verify=ctx,timeout=20,follow_redirects=True,trust_env=False) as c:
 for i in range(1,31):
  ds=f'F-B0046-{i:03d}'
  try:
   r=c.get('https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/'+ds,params={'Authorization':key,'format':'JSON'})
   rec={'id':ds,'status':r.status_code,'bytes':len(r.content)}
   if r.status_code==200:
    try:
     d=r.json().get('cwaopendata',{}); info=d.get('dataset',{}).get('datasetInfo',{});rec['description']=info.get('datasetDescription');rec['parameterSet']=info.get('parameterSet')
    except Exception:rec['parse']='non-json'
   out.append(rec)
  except Exception as e:out.append({'id':ds,'error':type(e).__name__})
(root/'research/f-b0046-probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print([(x['id'],x.get('status'),x.get('description')) for x in out if x.get('status')==200])
