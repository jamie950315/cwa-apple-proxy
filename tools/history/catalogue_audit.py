import asyncio,ssl,json,re,time
from pathlib import Path
import httpx,yaml
R=Path('/home/jamie/cwa-weather-proxy');K=dict(l.split('=',1) for l in (R/'.env').read_text().splitlines() if '=' in l)['CWA_API_KEY']
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
async def main():
 async with httpx.AsyncClient(verify=ctx,timeout=30,trust_env=False,follow_redirects=True) as c:
  r=await c.get('https://opendata.cwa.gov.tw/apidoc/v1');r.raise_for_status();(R/'research/openapi-current.yaml').write_text(r.text)
  doc=yaml.safe_load(r.text);out={'time':int(time.time()),'paths':{},'files':{},'links':{}}
  for path,ops in doc.get('paths',{}).items():
   if any(x in path for x in ['A-B006','O-A0002','W-C0033','C-B0024','F-D0047-061']):out['paths'][path]=ops
  for ds in ['A-B0062-001','A-B0062-002','A-B0063-001','A-B0063-002','F-C0041-001','F-C0041-002','F-C0041-003','F-C0041-004']:
   try:
    r=await c.get('https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/'+ds,params={'Authorization':K,'format':'JSON'})
    v={'http':r.status_code,'bytes':len(r.content)}
    if r.status_code==200:
     d=r.json();(R/'research'/('extended-'+ds+'.json')).write_text(json.dumps(d,ensure_ascii=False));root=d.get('cwaopendata',d);v['sent']=root.get('sent');v['keys']=list(root);v['dates']=sorted(set(re.findall(r'20\d\d-\d\d-\d\d',r.text)))[:3];v['lastDates']=sorted(set(re.findall(r'20\d\d-\d\d-\d\d',r.text)))[-3:]
    out['files'][ds]=v
   except Exception as e:out['files'][ds]={'error':type(e).__name__}
  for url in ['https://opendata.cwa.gov.tw/devManual/insrtuction','https://opendata.cwa.gov.tw/devManual/datalist','https://opendata.cwa.gov.tw/dist/js/content.3354d735.js','https://opendata.cwa.gov.tw/dist/content.js']:
   try:
    r=await c.get(url);text=r.text;(R/'research'/('web-'+url.rsplit('/',1)[-1]+'.txt')).write_text(text)
    matches=[]
    for term in ['graphql','linkedapi','LINKEDAPI','L-003','GraphQL']:
     for m in list(re.finditer(re.escape(term),text,re.I))[:8]:matches.append(text[max(0,m.start()-180):m.end()+280])
    out['links'][url]=matches
   except Exception as e:out['links'][url]={'error':type(e).__name__}
  (R/'research/catalogue-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
asyncio.run(main())
