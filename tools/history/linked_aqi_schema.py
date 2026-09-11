import asyncio,json,ssl,time
from pathlib import Path
import httpx
R=Path('/home/jamie/cwa-weather-proxy');key=dict(l.split('=',1) for l in (R/'.env').read_text().splitlines() if '=' in l)['CWA_API_KEY']
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
async def main():
    out={}
    async with httpx.AsyncClient(verify=ctx,timeout=20,trust_env=False) as c:
        for name in ['AQI','Query']:
            q='{ __type(name:"'+name+'") { name fields { name description args { name type { name kind ofType { name kind } } } type { name kind ofType { name kind } } } } }'
            r=await c.post('https://opendata.cwa.gov.tw/linked/graphql',headers={'Authorization':key},json={'query':q});r.raise_for_status();out[name]=r.json()
    (R/'research/linked-aqi-schema.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
asyncio.run(main())
