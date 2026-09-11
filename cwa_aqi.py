"""Taiwan MOENV air-quality observations distributed by CWA LinkedAPI.
The official Taiwan AQI value is preserved, with its source/scale identified.
"""
from cwa_model import number,epoch,distance
POLLUTANTS={'so2':('SO2','PARTS_PER_BILLION',1),'co':('CO','PARTS_PER_BILLION',1000),'o3':('OZONE','PARTS_PER_BILLION',1),'pm10':('PM10','MICROGRAMS_PER_CUBIC_METER',1),'pm2_5':('PM2_5','MICROGRAMS_PER_CUBIC_METER',1),'no2':('NO2','PARTS_PER_BILLION',1),'nox':('NOX','PARTS_PER_BILLION',1),'no':('NO','PARTS_PER_BILLION',1)}
PRIMARY={'PM2.5':'PM2_5','PM10':'PM10','O3':'OZONE','O₃':'OZONE','SO2':'SO2','NO2':'NO2','CO':'CO','細懸浮微粒':'PM2_5','懸浮微粒':'PM10','臭氧':'OZONE','二氧化氮':'NO2','二氧化硫':'SO2','一氧化碳':'CO'}
def normalize_aqi(data,lat,lon,now):
    if not isinstance(data,dict) or data.get('errors'):return None
    rows=data.get('data',{}).get('aqi') or []
    if isinstance(rows,dict):rows=[rows]
    candidates=[]
    for row in rows:
        index=number(row.get('aqi'),0,500);a=number(row.get('latitude'),-90,90);b=number(row.get('longitude'),-180,180);ts=epoch(str(row.get('publishtime','')).replace('/','-'))
        if index is None or a is None or b is None or ts is None or not -300<=now-ts<=5400:continue
        km=distance(lat,lon,a,b)
        if km<=100:candidates.append((km,row,index,ts,a,b))
    if not candidates:return None
    km,row,index,ts,a,b=min(candidates,key=lambda item:item[0])
    category=next((i+1 for i,limit in enumerate([50,100,150,200,300,500]) if index<=limit),6)
    pollutants=[]
    for name,(kind,units,scale) in POLLUTANTS.items():
        value=number(row.get(name),0,5000)
        if value is not None:pollutants.append({'pollutantType':kind,'units':units,'amount':value*scale})
    primary=PRIMARY.get(str(row.get('pollutant','')).strip(),'NOT_AVAILABLE')
    return {'index':int(round(index)),'categoryIndex':category,'isSignificant':index>100,'pollutants':pollutants,'primaryPollutant':primary,'scale':'TAIWAN_AQI','previousDayComparison':'UNKNOWN','metadata':{'attributionUrl':'https://airtw.moenv.gov.tw/','providerName':'環境部／中央氣象署 LinkedAPI','latitude':a,'longitude':b,'language':'zh-TW','readTime':int(now),'reportedTime':ts,'expireTime':int(now)+600,'sourceType':'STATION','temporarilyUnavailable':False},'provenance':{'source':'CWA LinkedAPI; original observations and AQI by Taiwan MOENV','stationName':row.get('sitename'),'stationId':row.get('siteid'),'distanceKm':round(km,3),'observedTime':ts,'status':row.get('status'),'indexDefinition':'Taiwan official AQI; never recomputed as US EPA AQI','coConversion':'ppm multiplied by 1000 to ppb'}}

# LinkedAPI uses slash-separated dates; preserve the shared timezone handling.
_cwa_aqi_iso_epoch = epoch
def epoch(value):
    return _cwa_aqi_iso_epoch(value.replace("/", "-") if isinstance(value, str) else value)
