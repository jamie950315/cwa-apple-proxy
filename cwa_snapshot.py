import asyncio,json,math,time
from cwa_client import Unavailable,ROOT
from cwa_model import choose_station,choose_rain_station,normalize_observation,normalize_rain,normalize_forecast,distance,visibility_meters,station_coordinates,epoch
from cwa_products import temperature_analysis,qpf_next_hour
from cwa_alerts import normalize_alerts
from cwa_astronomy import normalize_astronomy
from cwa_aqi import normalize_aqi
from cwa_nwp import normalize_nwp
COUNTY_IDS=json.loads((ROOT/'cwa_regions.json').read_text())
TOWNS=json.loads((ROOT/'town_index.json').read_text())

def forecast_town(lat,lon):
    closest=min(((distance(lat,lon,t['latitude'],t['longitude']),t) for t in TOWNS),key=lambda x:x[0])
    return closest if closest[0]<=60 else None

def nearest_visibility(stations,lat,lon,now):
    rows=[]
    for s in stations:
        xy=station_coordinates(s);ts=epoch(s.get('ObsTime',{}).get('DateTime'));v=visibility_meters(s.get('WeatherElement',{}).get('VisibilityDescription'))
        if xy and ts and v is not None and -300<=now-ts<=5400:
            d=distance(lat,lon,*xy)
            if d<=50:rows.append((d,v,s,ts))
    return min(rows,key=lambda x:x[0]) if rows else None

async def snapshot(store,lat,lon,country='TW'):
    now=time.time()
    if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('invalid coordinates')
    if country and country.upper()!='TW':raise Unavailable('outside Taiwan')
    if not (20<=lat<=27 and 117<=lon<=124):raise Unavailable('outside CWA coverage')
    ref=forecast_town(lat,lon)
    if not ref:raise Unavailable('outside forecast reference coverage')
    forecast_distance,place=ref;county=place['county'];n=COUNTY_IDS.get(county)
    ids=[f'F-D0047-{n:03d}',f'F-D0047-{n+2:03d}'] if n else []
    tasks=[store.get('O-A0003-001'),store.get('O-A0001-001'),store.get('O-A0002-001'),store.file_get('F-B0046-001'),store.file_get('O-A0038-003'),store.get('W-C0033-002'),store.get('A-B0062-001'),store.get('A-B0063-001'),store.linked_aqi()]+[store.get(i) for i in ids]
    data=await asyncio.gather(*tasks,return_exceptions=True)
    obs3,obs1,rain_data,qpf_data,temp_data,alert_detail_data,sun_data,moon_data,aqi_data=data[:9];forecast_data=data[9:]
    stations={}
    for d in [obs1,obs3]:
        if isinstance(d,Exception):continue
        for s in d.get('records',{}).get('Station',[]):
            if s.get('StationId'):stations[s['StationId']]=s
    chosen=choose_station(stations.values(),lat,lon,now=now)
    if not chosen:raise Unavailable('no fresh CWA station within 30 km')
    dist,s,ts=chosen;geo=s.get('GeoInfo',{});current=normalize_observation(s,ts)
    sources={k:'CWA station observation' for k in current if k!='observationTime'}
    analysis=None if isinstance(temp_data,Exception) else temperature_analysis(temp_data,lat,lon,s,now)
    if analysis and analysis['time']>=ts and dist>1.5:
        current['temperature']=analysis['temperature'];sources['temperature']=analysis['source']
    if current.get('dewPoint') is not None:sources['dewPoint']='CWA observed temperature/RH + Magnus derivation'
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

    vis=nearest_visibility(obs3.get('records',{}).get('Station',[]),lat,lon,now) if isinstance(obs3,dict) else None
    if vis:
        current['visibility']=vis[1];sources['visibility']='CWA visibility category midpoint, or lower bound for an open-ended category; estimate'
    current['_sources']=sources
    result={'source':'CWA','generatedAt':int(now),'requested':{'latitude':lat,'longitude':lon},'location':{'county':county,'forecastTown':place['town'],'forecastDistanceKm':round(forecast_distance,3),'stationCounty':geo.get('CountyName'),'stationTown':geo.get('TownName'),'stationName':s.get('StationName'),'stationId':s.get('StationId'),'stationDistanceKm':round(dist,3),'selection':'nearest fresh CWA station; forecast uses nearest CWA township reference'},'current':current,'shortTerm':{'points':[],'intervals':[]},'weekly':{'points':[],'intervals':[]},'rain':None,'nowcast':None,'weatherAlerts':normalize_alerts(alert_detail_data,county,lat,lon,now) if isinstance(alert_detail_data,dict) else None,'astronomy':normalize_astronomy(sun_data,moon_data,county),'airQuality':normalize_aqi(aqi_data,lat,lon,now),'nwp':normalize_nwp(store.model_product(),county,place['town'],now),'provenance':{'observationTime':ts,'units':{'temperature':'C','windSpeed':'km/h','windGust':'km/h','humidity':'fraction','pressure':'hPa','precipitation':'mm','visibility':'m'},'forecastDatasets':[]}}
    if analysis:
        analysis['usedForCurrent']=current['_sources'].get('temperature')==analysis['source']
        result['provenance']['temperatureAnalysis']=analysis
    if vis:result['provenance']['visibilityStation']={'stationId':vis[2].get('StationId'),'stationName':vis[2].get('StationName'),'distanceKm':round(vis[0],3),'observationTime':vis[3]}
    if isinstance(rain_data,dict):
        rc=choose_rain_station(rain_data.get('records',{}).get('Station',[]),lat,lon,now=now)
        if rc:
            rd,rs,rts=rc;rain=normalize_rain(rs,rts);rgeo=rs.get('GeoInfo',{})
            rain.update({'stationId':rs.get('StationId'),'stationName':rs.get('StationName'),'stationTown':rgeo.get('TownName'),'distanceKm':round(rd,3)})
            result['rain']=rain;result['provenance']['rainStation']={k:rain[k] for k in ['stationId','stationName','distanceKm','observationTime'] if k in rain}
    if not isinstance(qpf_data,Exception):
        qpf=qpf_next_hour(qpf_data,lat,lon,s,now)
        if qpf:result['nowcast']=qpf;result['provenance']['nextHourQPF']=qpf
    for key,dataset,d in zip(['shortTerm','weekly'],ids,forecast_data):
        if isinstance(d,Exception):continue
        groups=d.get('records',{}).get('Locations',[])
        if not groups or groups[0].get('LocationsName','').replace('台','臺')!=county:continue
        loc=next((l for g in groups for l in g.get('Location',[]) if l.get('LocationName')==place['town']),None)
        if not loc:continue
        result[key]=normalize_forecast(loc)
        result['provenance']['forecastDatasets'].append({'id':dataset,'town':loc.get('LocationName'),'distanceKm':round(forecast_distance,3),'selection':'nearest CWA township forecast reference point'})
    return result
