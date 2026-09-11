"""Authenticated CWA downloads with bounded concurrency, validation and disk cache."""
import asyncio,json,os,ssl,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parent
REST_ALLOWED={'O-A0001-001','O-A0002-001','O-A0003-001','W-C0033-001','W-C0033-002','A-B0062-001','A-B0063-001'}|{f'F-D0047-{n:03d}' for n in range(1,92,2)}
FILE_ALLOWED={'F-B0046-001','O-A0038-003','M-A0064-000','M-A0064-006'}
class Unavailable(Exception):pass
class Store:
    def __init__(self):
        cfg=dict(l.split('=',1) for l in (ROOT/'.env').read_text().splitlines() if l and not l.startswith('#') and '=' in l)
        self.key=os.getenv('CWA_API_KEY',cfg.get('CWA_API_KEY',''))
        if not self.key:raise RuntimeError('CWA_API_KEY required')
        self.model_cache=None;self.cache={};self.locks={};self.errors={};self.fetch_count=0
        ctx=ssl.create_default_context()
        # CWA's chain currently needs OpenSSL legacy-extension compatibility; certificate + hostname checks stay enabled.
        if hasattr(ssl,'VERIFY_X509_STRICT'):ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        self.client=httpx.AsyncClient(verify=ctx,timeout=httpx.Timeout(20,connect=6),follow_redirects=False,trust_env=False)
        self.semaphore=asyncio.Semaphore(4)
    async def close(self):await self.client.aclose()
    def _ttl(self,key):
        if key in {'O-A0001-001','O-A0002-001','O-A0003-001'}:return 300
        if key=='file:F-B0046-001':return 300
        if key=='file:O-A0038-003':return 1800
        if key.startswith('W-C0033-'):return 300
        if key.startswith('F-D0047-'):return 1800
        if key.startswith('A-B006'):return 43200
        if key=='linked:aqi':return 600
        return 21600
    def _path(self,key):return ROOT/'data'/((key.replace(':','-'))+'.json')
    def _disk_entry(self,key):
        path=self._path(key)
        if not path.exists():return None
        try:return (path.stat().st_mtime,json.loads(path.read_text()))
        except (OSError,ValueError):return None
    async def _cached(self,key,fetch):
        ttl=self._ttl(key)
        async with self.locks.setdefault(key,asyncio.Lock()):
            now=time.time();entry=self.cache.get(key)
            if not entry:
                entry=self._disk_entry(key)
                if entry:self.cache[key]=entry
            if entry and now-entry[0]<ttl:return entry[1]
            if now-self.errors.get(key,{}).get('time',0)<60:
                if entry and now-entry[0]<3600:return entry[1]
                raise Unavailable('CWA retry backoff')
            try:
                data=await fetch()
                path=self._path(key);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False));tmp.replace(path)
                self.cache[key]=(time.time(),data);self.fetch_count+=1;self.errors.pop(key,None)
                return data
            except (httpx.HTTPError,ValueError,OSError,KeyError) as e:
                self.errors[key]={'time':time.time(),'type':type(e).__name__}
                stale_limit=1800 if key=='file:F-B0046-001' else 7200 if key.startswith('file:') else 3600
                if entry and now-entry[0]<stale_limit:return entry[1]
                raise Unavailable('CWA data unavailable') from None
    async def get(self,dataset):
        if dataset not in REST_ALLOWED:raise ValueError('unknown dataset')
        async def fetch():
            async with self.semaphore:
                params={'Authorization':self.key,'format':'JSON'}
                if dataset.startswith('A-B006'):
                    today=datetime.now(timezone(timedelta(hours=8))).date()
                    params.update(timeFrom=str(today-timedelta(days=1)),timeTo=str(today+timedelta(days=15)))
                r=await self.client.get('https://opendata.cwa.gov.tw/api/v1/rest/datastore/'+dataset,params=params)
                r.raise_for_status()
                if len(r.content)>20_000_000:raise ValueError('response too large')
                data=r.json()
            if str(data.get('success')).lower()!='true' or not data.get('records'):raise ValueError('missing records')
            return data
        return await self._cached(dataset,fetch)
    async def file_get(self,dataset):
        if dataset not in FILE_ALLOWED:raise ValueError('unknown file dataset')
        key='file:'+dataset
        async def fetch():
            async with self.semaphore:
                r=await self.client.get('https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/'+dataset,params={'Authorization':self.key,'format':'JSON'},follow_redirects=True)
                r.raise_for_status()
                if len(r.content)>12_000_000:raise ValueError('file response too large')
                data=r.json()
            if not data.get('cwaopendata'):raise ValueError('missing cwaopendata')
            return data
        return await self._cached(key,fetch)
    async def linked_aqi(self):
        async def fetch():
            query='{ aqi { sitename county aqi pollutant status so2 co o3 pm10 pm2_5 no2 nox no publishtime longitude latitude siteid } }'
            async with self.semaphore:
                r=await self.client.post('https://opendata.cwa.gov.tw/linked/graphql',headers={'Authorization':self.key,'Accept':'application/json'},json={'query':query})
                r.raise_for_status()
                if len(r.content)>2_000_000:raise ValueError('AQI response size')
                data=r.json()
                if data.get('errors') or not data.get('data',{}).get('aqi'):raise ValueError('AQI GraphQL error or empty response')
                return data
        return await self._cached('linked:aqi',fetch)
    def model_product(self):
        # One fixed local product written by the validated GRIB worker; never a user-selected path.
        path=ROOT/'data/model-wrf.json'
        try:
            stat=path.stat()
            if stat.st_size>2_000_000:return None
            if not self.model_cache or self.model_cache[0]!=stat.st_mtime_ns:
                self.model_cache=(stat.st_mtime_ns,json.loads(path.read_text()))
            return self.model_cache[1]
        except (OSError,ValueError):return None
    def health(self):
        return {'fetchCount':self.fetch_count,'cache':{k:{'ageSeconds':round(time.time()-v[0])} for k,v in self.cache.items()},'errors':self.errors}
