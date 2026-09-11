"""Refresh bounded WRF-3km surface subsets outside the Weather request path.
HTTP Range downloads are validated as GRIB2; complete 180 MB files are never
fetched by this worker. APCP=discipline 0/category 1/number 8, kg/m² = mm water.
"""
import asyncio,json,math,time,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
import httpx,eccodes as ec
ROOT=Path(__file__).resolve().parent
BASE='https://cwaopendata.s3.ap-northeast-1.amazonaws.com/Model/'
HOURS=list(range(6,73,6))
FIELDS={'apcp':(142629590,2338214,0,1,8),'pressure':(177702464,2338190,0,3,1)}
TOWNS=json.loads((ROOT/'town_index.json').read_text())
def decode(blob,kind,hour,geometry):
    if blob[:4]!=b'GRIB' or blob[7]!=2 or int.from_bytes(blob[8:16],'big')!=len(blob):raise ValueError('GRIB message framing')
    g=ec.codes_new_from_message(blob)
    try:
        expected=FIELDS[kind][2:]
        if tuple(ec.codes_get(g,k) for k in ['discipline','parameterCategory','parameterNumber'])!=expected:raise ValueError('GRIB parameter identity')
        if ec.codes_get(g,'endStep')!=hour or ec.codes_get(g,'stepUnits')!=1:raise ValueError('GRIB forecast lead')
        initial=int(datetime.strptime(str(ec.codes_get(g,'dataDate'))+f'{ec.codes_get(g,"dataTime"):04d}','%Y%m%d%H%M').replace(tzinfo=timezone.utc).timestamp())
        start=ec.codes_get(g,'startStep')
        if kind=='apcp' and (start!=0 or ec.codes_get(g,'stepType')!='accum'):raise ValueError('APCP accumulation origin')
        if kind=='pressure' and ec.codes_get(g,'typeOfLevel')!='meanSea':raise ValueError('Pressure level')
        signature=ec.codes_get(g,'md5Section3')
        if signature not in geometry:
            near=ec.codes_grib_find_nearest_multiple(g,False,[t['latitude'] for t in TOWNS],[t['longitude'] for t in TOWNS])
            geometry[signature]=[{'index':int(p['index']),'distanceKm':float(p['distance']),'latitude':float(p['lat']),'longitude':float(p['lon'])} for p in near]
        geo=geometry[signature];values=ec.codes_get_elements(g,'values',[p['index'] for p in geo])
        missing=ec.codes_get(g,'missingValue');clean=[]
        for v,p in zip(values,geo):
            v=float(v)
            if not math.isfinite(v) or v==missing or p['distanceKm']>10:clean.append(None);continue
            if kind=='pressure':v/=100
            clean.append(v if ((0<=v<=5000) if kind=='apcp' else 850<=v<=1100) else None)
        return {'initialTime':initial,'forecastTime':initial+hour*3600,'leadHours':hour,'values':clean,'geometry':signature}
    finally:ec.codes_release(g)
async def main():
    cache_dir=ROOT/'data/model-subsets';cache_dir.mkdir(exist_ok=True)
    out={'version':1,'generatedAt':int(time.time()),'source':'CWA WRF-3km M-A0064 GRIB2','fields':{},'geometry':{},'errors':{},'downloadBytes':0}
    semaphore=asyncio.Semaphore(2)
    async with httpx.AsyncClient(timeout=httpx.Timeout(40,connect=8),trust_env=False) as client:
        async def one(hour):
            async with semaphore:
                dataset=f'M-A0064-{hour:03d}';url=BASE+dataset+'.grb2'
                try:
                    head=await client.head(url);head.raise_for_status();etag=head.headers.get('etag','')
                    if not etag:raise ValueError('Missing ETag')
                    for kind,(offset,length,*_) in FIELDS.items():
                        if kind=='pressure':offset=int(head.headers['content-length'])-2*length
                        key=f'{dataset}-{kind}';path=cache_dir/(key+'.grib2');meta=cache_dir/(key+'.json')
                        old=json.loads(meta.read_text()) if meta.exists() else {}
                        if old.get('etag')==etag and path.exists():blob=path.read_bytes()
                        else:
                            async with client.stream('GET',url,headers={'Range':f'bytes={offset}-{offset+length-1}','If-Match':etag}) as r:
                                if r.status_code!=206:raise ValueError('Server did not return bounded range: '+str(r.status_code))
                                if not r.headers.get('content-range','').startswith(f'bytes {offset}-{offset+length-1}/'):raise ValueError('Content-Range mismatch')
                                blob=await r.aread()
                            if len(blob)!=length:raise ValueError('Range size mismatch')
                            out['downloadBytes']+=len(blob)
                        data=decode(blob,kind,hour,out['geometry'])
                        path.write_bytes(blob);meta.write_text(json.dumps({'etag':etag,'sha256':hashlib.sha256(blob).hexdigest()}))
                        out['fields'].setdefault(kind,[]).append(data)
                except Exception as e:out['errors'][dataset]=type(e).__name__+': '+str(e)[:120]
        await asyncio.gather(*(one(h) for h in HOURS))
    for rows in out['fields'].values():rows.sort(key=lambda r:(r['initialTime'],r['leadHours']))
    out['towns']=[{'county':t['county'],'town':t['town']} for t in TOWNS]
    if not out['fields']:raise RuntimeError('No validated model subsets')
    path=ROOT/'data/model-wrf.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(out,ensure_ascii=False));tmp.replace(path)
    print(json.dumps({'fields':{k:len(v) for k,v in out['fields'].items()},'errors':out['errors'],'downloadBytes':out['downloadBytes'],'towns':len(TOWNS)},ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
