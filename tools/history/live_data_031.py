"""Read-only live CWA validation for release 0.3.1."""
import asyncio,json,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
from cwa_client import Store
from cwa_snapshot import snapshot
R=Path('/home/jamie/cwa-weather-proxy')
async def main():
    store=Store();out=[]
    try:
        for name,lat,lon in [('臺北',25.09,121.56),('臺南',22.99,120.207),('桃園',24.991,121.311)]:
            start=time.monotonic();s=await snapshot(store,lat,lon);elapsed=time.monotonic()-start
            (R/'research'/('live031-'+name+'.json')).write_text(json.dumps(s,ensure_ascii=False))
            today=datetime.now(timezone(timedelta(hours=8))).date().isoformat()
            astro=next((d for d in s['astronomy']['days'] if d['date']==today),None)
            assert astro and 'sunrise' in astro and 'sunset' in astro,('Current-date astronomy absent',name)
            assert s['current']['observationTime']>time.time()-5400
            assert len(s['shortTerm']['points'])>20
            assert s['rain'] and 'past24h' in s['rain']
            assert s.get('airQuality') and 0<=s['airQuality']['index']<=500
            assert s.get('nwp') and len(s['nwp']['rainIntervals'])>=10
            out.append({'name':name,'seconds':round(elapsed,3),'current':s['current'],'rain':s['rain'],'nowcast':s['nowcast'],'astronomyToday':astro,'astronomyDays':len(s['astronomy']['days']),'station':s['location'],'provenance':s['provenance']})
        (R/'reports/live-data-031.json').write_text(json.dumps({'time':int(time.time()),'results':out,'health':store.health()},ensure_ascii=False,indent=2))
        print(json.dumps({'passed':len(out),'astronomyDate':today},ensure_ascii=False))
    finally:await store.close()
asyncio.run(main())
