from pathlib import Path
R=Path('/home/jamie/cwa-weather-proxy')
p=R/'cwa_client.py';s=p.read_text();s=s.replace('import asyncio,json,os,ssl,time','import asyncio,json,os,ssl,time\nfrom datetime import datetime,timedelta,timezone')
s=s.replace("'W-C0033-002'}", "'W-C0033-002','A-B0062-001','A-B0063-001'}")
s=s.replace("if key.startswith('F-D0047-'):return 1800", "if key.startswith('F-D0047-'):return 1800\n        if key.startswith('A-B006'):return 43200")
s=s.replace("r=await self.client.get('https://opendata.cwa.gov.tw/api/v1/rest/datastore/'+dataset,params={'Authorization':self.key,'format':'JSON'})", "params={'Authorization':self.key,'format':'JSON'}\n                if dataset.startswith('A-B006'):\n                    today=datetime.now(timezone(timedelta(hours=8))).date()\n                    params.update(timeFrom=str(today-timedelta(days=1)),timeTo=str(today+timedelta(days=15)))\n                r=await self.client.get('https://opendata.cwa.gov.tw/api/v1/rest/datastore/'+dataset,params=params)")
p.write_text(s)
p=R/'cwa_products.py';s=p.read_text().replace('import math,time','import math,time,re\nfrom collections import OrderedDict').replace('_GRID_CACHE={}','_GRID_CACHE=OrderedDict()').replace('cached=_GRID_CACHE.get(key)','key=(*key,hash(text))\n    cached=_GRID_CACHE.get(key)').replace('_GRID_CACHE.clear();_GRID_CACHE[key]=vals','_GRID_CACHE[key]=vals\n    while len(_GRID_CACHE)>4:_GRID_CACHE.popitem(last=False)')
s=s.replace("left,bottom=float(meta['StartPointLongitude']),float(meta['StartPointLatitude'])", "left,bottom=float(meta['StartPointLongitude']),float(meta['StartPointLatitude'])\n        origin='parameterSet'\n        desc=d['contents'].get('contentDescription','')\n        match=re.search(r'東經[為\\s]*([0-9.]+).*?北緯[為\\s]*([0-9.]+)',desc)\n        if match:\n            documented_lon,documented_lat=map(float,match.groups())\n            if abs(documented_lon-left)<0.1 and abs(documented_lat-bottom)<0.1:\n                left,bottom=documented_lon,documented_lat;origin='contentDescription explicit first cell'")
s=s.replace("'start':start,'end':start+3600", "'originDefinition':origin,'start':start,'end':start+3600")
p.write_text(s)
p=R/'cwa_snapshot.py';s=p.read_text().replace('from cwa_alerts import normalize_alerts','from cwa_alerts import normalize_alerts\nfrom cwa_astronomy import normalize_astronomy')
s=s.replace("store.get('W-C0033-002')]+", "store.get('W-C0033-002'),store.get('A-B0062-001'),store.get('A-B0063-001')]+")
s=s.replace("alert_detail_data=data[:7];forecast_data=data[7:]", "alert_detail_data,sun_data,moon_data=data[:9];forecast_data=data[9:]")
s=s.replace("if analysis:\n        current['temperature']", "if analysis and analysis['time']>=ts and dist>1.5:\n        current['temperature']")
s=s.replace("else {'alerts':[],'reportedTime':int(now)},'provenance'", "else None,'astronomy':normalize_astronomy(sun_data,moon_data,county),'provenance'")
s=s.replace("if analysis:result['provenance']['temperatureAnalysis']=analysis", "if analysis:\n        analysis['usedForCurrent']=current['_sources'].get('temperature')==analysis['source']\n        result['provenance']['temperatureAnalysis']=analysis")
needle="    if current.get('dewPoint') is not None:sources['dewPoint']='CWA observed temperature/RH + Magnus derivation'"
s=s.replace(needle,needle+'''
    # Apple pressure is reduced to mean sea level; CWA AirPressure is station pressure.
    station_pressure=current.pop('pressure',None)
    if station_pressure is not None:
        current['stationPressure']=station_pressure
        try:
            altitude=float(geo['StationAltitude']);t=current['temperature']+273.15
            if -100<=altitude<=1000:
                vapour=(current.get('humidity',0))*6.112*math.exp(17.67*(t-273.15)/(t-29.65))
                tv=t*(1+0.61*0.622*vapour/(station_pressure-vapour))+0.00325*altitude
                reduced=station_pressure*math.exp(9.80665*altitude/(287.05*tv))
                if 850<=reduced<=1100:
                    current['pressure']=reduced;sources['pressure']='CWA station P/T/RH/height; hypsometric sea-level estimate'
        except (KeyError,TypeError,ValueError,ZeroDivisionError):pass
    gust_time=epoch(s.get('WeatherElement',{}).get('GustInfo',{}).get('Occurred_at',{}).get('DateTime'))
    if 'windGust' in current and (gust_time is None or not -300<=now-gust_time<=1800):
        current['earlierPeakGust']=current.pop('windGust');sources.pop('windGust',None)
''')
p.write_text(s)
p=R/'api.py';s=p.read_text().replace("VERSION='0.3.0'","VERSION='0.3.1'");s=s.replace("store.get('W-C0033-002'),", "store.get('W-C0033-002'),store.get('A-B0062-001'),store.get('A-B0063-001'),")
p.write_text(s)
p=R/'mapper.mjs';s=p.read_text();s=s.replace("const before=changes.length,selected=weekly.filter", "const astro=snapshot.astronomy?.days?.find(p=>p.date===key);\n   if(astro)for(const k of ['sunrise','sunset','solarNoon','sunriseCivil','sunsetCivil','moonrise','moonset'])set(day,k,astro[k],`day[${i}]`,astro._sources?.[k]||'CWA calendar astronomy');\n   const before=changes.length,selected=weekly.filter")
s=s.replace("'astronomy pending current-year CWA table validation'", "'moon phase/illumination and nautical/astronomical twilight where CWA time tables contain no equivalent'")
s=s.replace("  const a=snapshot.weatherAlerts,reported=", "  const a=snapshot.weatherAlerts,reported=")
s=s.replace("  output=WeatherKit2.encode(new ByteBuffer(output),{weatherAlerts:obj});", "  const upstream=WeatherKit2.decode(new ByteBuffer(output),['weatherAlerts']).weatherAlerts;\n  const ids=new Set(obj.alerts.map(p=>p.id));\n  obj.alerts=[...(upstream?.alerts||[]).filter(p=>!ids.has(p.id)&&p.eventSource!=='CWA'),...obj.alerts];\n  output=WeatherKit2.encode(new ByteBuffer(output),{weatherAlerts:obj});")
p.write_text(s)
print('source patches staged')
