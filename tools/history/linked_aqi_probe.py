"""Validate the CWA LinkedAPI documented in Taipei DOIT's public RideFlow example."""
import asyncio,json,ssl,time
from pathlib import Path
import httpx
R=Path('/home/jamie/cwa-weather-proxy');key=dict(l.split('=',1) for l in (R/'.env').read_text().splitlines() if '=' in l)['CWA_API_KEY']
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
async def main():
    out={'time':int(time.time()),'endpoint':'https://opendata.cwa.gov.tw/linked/graphql','requests':[]}
    queries=['{ aqi(longitude:121.56,latitude:25.09) { sitename aqi status __typename } }','{ __schema { queryType { name fields { name type { name kind ofType { name kind ofType { name kind } } } } } } }']
    async with httpx.AsyncClient(verify=ctx,timeout=20,trust_env=False) as c:
        for q in queries:
            try:
                r=await c.post(out['endpoint'],headers={'Authorization':key,'Accept':'application/json'},json={'query':q})
                result={'http':r.status_code,'query':q,'bytes':len(r.content)}
                try:result['response']=r.json()
                except ValueError:result['prefix']=r.text[:300]
                out['requests'].append(result)
            except Exception as e:out['requests'].append({'error':type(e).__name__})
    (R/'research/linked-aqi-probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
asyncio.run(main())
