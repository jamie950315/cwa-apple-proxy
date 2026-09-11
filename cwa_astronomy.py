"""CWA calendar-day solar/lunar times, using explicit current date windows."""
from cwa_model import epoch
SUN_FIELDS={'SunRiseTime':'sunrise','SunSetTime':'sunset','SunTransitTime':'solarNoon','BeginCivilTwilightTime':'sunriseCivil','EndCivilTwilightTime':'sunsetCivil'}
MOON_FIELDS={'MoonRiseTime':'moonrise','MoonSetTime':'moonset'}
def normalize_astronomy(sun,moon,county):
    days={}
    for dataset,data,mapping in [('A-B0062-001',sun,SUN_FIELDS),('A-B0063-001',moon,MOON_FIELDS)]:
        if not isinstance(data,dict):continue
        locs=data.get('records',{}).get('locations',{}).get('location',[])
        if isinstance(locs,dict):locs=[locs]
        for loc in locs:
            if loc.get('CountyName','').replace('台','臺')!=county:continue
            for row in loc.get('time',[]):
                date=row.get('Date','')
                if len(date)!=10:continue
                d=days.setdefault(date,{'date':date,'_sources':{}})
                for src,dst in mapping.items():
                    value=row.get(src)
                    if not isinstance(value,str) or not value or value=='--':continue
                    t=epoch(date+'T'+value+(':00' if len(value)==5 else '')+'+08:00')
                    if t is not None:d[dst]=t;d['_sources'][dst]='CWA '+dataset+' county reference calendar day'
    return {'county':county,'days':list(days.values()),'spatialScope':'county reference point'}
