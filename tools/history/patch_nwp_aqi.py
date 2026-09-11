from pathlib import Path
R=Path('/home/jamie/cwa-weather-proxy')
p=R/'cwa_client.py';s=p.read_text();s=s.replace("self.cache={};self.locks={};", "self.model_cache=None;self.cache={};self.locks={};")
s=s.replace("if key.startswith('A-B006'):return 43200", "if key.startswith('A-B006'):return 43200\n        if key=='linked:aqi':return 600")
needle='    def health(self):'
assert needle in s
s=s.replace(needle,'''    async def linked_aqi(self):
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
''' +needle)
p.write_text(s)
p=R/'cwa_snapshot.py';s=p.read_text().replace('from cwa_astronomy import normalize_astronomy','from cwa_astronomy import normalize_astronomy\nfrom cwa_aqi import normalize_aqi\nfrom cwa_nwp import normalize_nwp')
s=s.replace("store.get('A-B0063-001')]+", "store.get('A-B0063-001'),store.linked_aqi()]+")
s=s.replace("sun_data,moon_data=data[:9];forecast_data=data[9:]", "sun_data,moon_data,aqi_data=data[:10];forecast_data=data[10:]")
s=s.replace("'astronomy':normalize_astronomy(sun_data,moon_data,county),'provenance'", "'astronomy':normalize_astronomy(sun_data,moon_data,county),'airQuality':normalize_aqi(aqi_data,lat,lon,now),'nwp':normalize_nwp(store.model_product(),county,place['town'],now),'provenance'")
s=s.replace("'CWA synoptic visibility category converted to metres'", "'CWA visibility category midpoint, or lower bound for an open-ended category; estimate'")
p.write_text(s)
p=R/'api.py';s=p.read_text().replace("store.get('A-B0063-001'),return_exceptions", "store.get('A-B0063-001'),store.linked_aqi(),return_exceptions")
s=s.replace("result['notification']=read_json(ROOT/'data/notification-last.json',{})", "result['notification']=read_json(ROOT/'data/notification-last.json',{})\n    result['notificationTest']=read_json(ROOT/'reports/ntfy-timeout-selftest.json',{})")
s += "\n@app.get('/audit')\nasync def audit():return read_json(ROOT/'reports/source-audit.json',{'status':'report being updated'})\n"
p.write_text(s)
print('CWA LinkedAPI and validated local NWP adapters staged')
