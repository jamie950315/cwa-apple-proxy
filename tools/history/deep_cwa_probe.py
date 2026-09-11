import asyncio, httpx, json, ssl, os, pathlib, time, urllib.parse
ROOT=pathlib.Path('/home/jamie/cwa-weather-proxy')
cfg=dict(l.split('=',1) for l in (ROOT/'.env').read_text().splitlines() if '=' in l)
KEY=cfg['CWA_API_KEY']
ctx=ssl.create_default_context()
if hasattr(ssl,'VERIFY_X509_STRICT'): ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
REST='https://opendata.cwa.gov.tw/api/v1/rest/datastore/'
FILE='https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/'
DATASETS=['O-A0001-001','O-A0002-001','O-A0003-001','F-D0047-061','W-C0033-001','W-C0033-002','A-B0062-001','A-B0063-001','C-B0024-001']
FILESETS=['F-B0046-001','O-A0038-003','F-D0047-093','M-A0064-000','M-A0064-006']

def shape(x, depth=0):
    if depth>3:return type(x).__name__
    if isinstance(x,dict):return {k:shape(v,depth+1) for k,v in list(x.items())[:30]}
    if isinstance(x,list):return {'len':len(x),'first':shape(x[0],depth+1) if x else None}
    return type(x).__name__

async def main():
 async with httpx.AsyncClient(verify=ctx,timeout=httpx.Timeout(60,connect=10),follow_redirects=True,trust_env=False) as c:
  out={'time':time.time(),'rest':{},'file':{}}
  for ds in DATASETS:
   try:
    r=await c.get(REST+ds,params={'Authorization':KEY,'format':'JSON'})
    rec={'status':r.status_code,'bytes':len(r.content),'type':r.headers.get('content-type')}
    if r.status_code==200:
     d=r.json(); rec['success']=d.get('success');rec['shape']=shape(d.get('records',{}));
     (ROOT/'research'/f'probe-{ds}.json').write_text(json.dumps(d,ensure_ascii=False))
    else: rec['body']=r.text[:500]
    out['rest'][ds]=rec
   except Exception as e:out['rest'][ds]={'error':type(e).__name__+': '+str(e)[:200]}
  for ds in FILESETS:
   try:
    r=await c.get(FILE+ds,params={'Authorization':KEY,'format':'JSON'})
    rec={'status':r.status_code,'bytes':len(r.content),'type':r.headers.get('content-type'),'url':str(r.url)}
    if r.status_code==200 and len(r.content)<30_000_000:
     try:
      d=r.json();rec['shape']=shape(d);(ROOT/'research'/f'file-{ds}.json').write_text(json.dumps(d,ensure_ascii=False))
     except Exception as e:
      rec['prefix']=r.text[:500]
    out['file'][ds]=rec
   except Exception as e:out['file'][ds]={'error':type(e).__name__+': '+str(e)[:200]}
  (ROOT/'research/deep-cwa-probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
  print(json.dumps(out,ensure_ascii=False,indent=2))
asyncio.run(main())
