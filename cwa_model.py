"""CWA numeric validation, observation normalization and geographic helpers."""
import math,time
from datetime import datetime,timezone,timedelta
TZ=timezone(timedelta(hours=8))
def number(value,lo=-math.inf,hi=math.inf):
    try:
        if isinstance(value,bool):return None
        n=float(value);return n if math.isfinite(n) and lo<=n<=hi else None
    except (ValueError,TypeError):return None
def precipitation_number(value):
    return number(value,0,3000)
def precipitation_trace(value):
    return isinstance(value,str) and value.strip().upper()=='T'
def epoch(value):
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None:dt=dt.replace(tzinfo=TZ)
        return int(dt.timestamp())
    except (ValueError,TypeError,AttributeError):return None
def distance(a,b,c,d):
    la,lb=math.radians(a),math.radians(c)
    h=math.sin((lb-la)/2)**2+math.cos(la)*math.cos(lb)*math.sin(math.radians(d-b)/2)**2
    return 6371.0088*2*math.asin(min(1,math.sqrt(h)))
def clean(d):return {k:v for k,v in d.items() if v is not None}
def station_coordinates(s):
    c=next((c for c in s.get('GeoInfo',{}).get('Coordinates',[]) if c.get('CoordinateName')=='WGS84'),None)
    if not c:return None
    a,b=number(c.get('StationLatitude'),-90,90),number(c.get('StationLongitude'),-180,180)
    return (a,b) if a is not None and b is not None else None
def _choose(stations,lat,lon,validator,now,max_distance,max_age):
    valid=[]
    for s in stations:
        xy=station_coordinates(s);ts=epoch(s.get('ObsTime',{}).get('DateTime'))
        if xy is None or ts is None or not -300<=now-ts<=max_age or not validator(s):continue
        d=distance(lat,lon,*xy)
        if d<=max_distance:valid.append((d,s,ts))
    return min(valid,key=lambda t:t[0]) if valid else None
def choose_station(stations,lat,lon,now=None,max_distance=30,max_age=5400):
    now=time.time() if now is None else now
    return _choose(stations,lat,lon,lambda s:number(s.get('WeatherElement',{}).get('AirTemperature'),-60,65) is not None,now,max_distance,max_age)
def choose_rain_station(stations,lat,lon,now=None,max_distance=30,max_age=1800):
    now=time.time() if now is None else now
    return _choose(stations,lat,lon,lambda s:any(precipitation_number(v) is not None or precipitation_trace(v) for v in (s.get('RainfallElement',{}).get(k,{}).get('Precipitation') for k in ['Past10Min','Past1hr','Past3hr','Past6Hr','Past12hr','Past24hr'])),now,max_distance,max_age)
def dewpoint_c(temp,rh_fraction):
    if temp is None or rh_fraction is None or not 0<rh_fraction<=1:return None
    a,b=17.625,243.04;g=math.log(rh_fraction)+a*temp/(b+temp)
    return b*g/(a-g)
def visibility_meters(value):
    if not isinstance(value,str):return None
    s=value.strip().replace('公里','')
    if s.startswith('>'):
        v=number(s[1:],0,100);return v*1000 if v is not None else None
    if '-' in s:
        try:a,b=map(float,s.split('-',1));return (a+b)*500
        except ValueError:return None
    v=number(s,0,100);return v*1000 if v is not None else None
def normalize_observation(s,ts):
    w=s.get('WeatherElement',{});wind=number(w.get('WindSpeed'),0,150);rh=number(w.get('RelativeHumidity'),0,100);temp=number(w.get('AirTemperature'),-60,65)
    gust=number(w.get('GustInfo',{}).get('PeakGustSpeed'),0,200);pressure=number(w.get('AirPressure'),400,1100)
    visibility=visibility_meters(w.get('VisibilityDescription'))
    return clean({'observationTime':ts,'temperature':temp,'humidity':rh/100 if rh is not None else None,'dewPoint':dewpoint_c(temp,rh/100 if rh is not None else None),'windSpeed':wind*3.6 if wind is not None else None,'windDirection':number(w.get('WindDirection'),0,360),'windGust':gust*3.6 if gust is not None else None,'pressure':pressure,'visibility':visibility,'uvIndex':number(w.get('UVIndex'),0,30),'weatherText':w.get('Weather') if w.get('Weather') not in ['-99','',None] else None})
def normalize_rain(s,ts):
    r=s.get('RainfallElement',{});out={'observationTime':ts}
    keys={'Past10Min':'past10m','Past1hr':'past1h','Past3hr':'past3h','Past6Hr':'past6h','Past12hr':'past12h','Past24hr':'past24h','Now':'today'}
    traces=[]
    for src,dst in keys.items():
        raw=r.get(src,{}).get('Precipitation');v=precipitation_number(raw)
        if v is not None:out[dst]=v
        elif precipitation_trace(raw):traces.append(dst)
    if traces:out['traceFields']=traces
    return out
def normalize_daily_extremes(s,ts,current_temperature,now=None):
    now=time.time() if now is None else now
    if not isinstance(ts,(int,float)) or not math.isfinite(ts) or not -300<=now-ts<=5400:return None
    daily=s.get('WeatherElement',{}).get('DailyExtreme',{})
    high=daily.get('DailyHigh',{}).get('TemperatureInfo',{});low=daily.get('DailyLow',{}).get('TemperatureInfo',{})
    maximum=number(high.get('AirTemperature'),-60,65);minimum=number(low.get('AirTemperature'),-60,65)
    current=number(current_temperature,-60,65)
    maximum_time=epoch(high.get('Occurred_at',{}).get('DateTime'));minimum_time=epoch(low.get('Occurred_at',{}).get('DateTime'))
    if any(v is None for v in (maximum,minimum,current,maximum_time,minimum_time)):return None
    observation=datetime.fromtimestamp(ts,TZ);date=observation.date()
    if datetime.fromtimestamp(maximum_time,TZ).date()!=date or datetime.fromtimestamp(minimum_time,TZ).date()!=date:return None
    if maximum_time>ts or minimum_time>ts or not minimum<=current<=maximum:return None
    start=int(datetime.combine(date,datetime.min.time(),TZ).timestamp())
    out={'date':date.isoformat(),'start':start,'end':start+86400,'observationTime':int(ts),'temperatureMax':maximum,'temperatureMin':minimum,'temperatureMaxTime':maximum_time,'temperatureMinTime':minimum_time,'source':'CWA station DailyExtreme observation'}
    if s.get('StationId'):out['stationId']=s['StationId']
    return out
def locations(data):
    rec=data.get('records',{});return [loc for g in rec.get('Locations',rec.get('locations',[])) for loc in g.get('Location',g.get('location',[]))]
def nearest_location(data,lat,lon,max_distance=60):
    candidates=[]
    for loc in locations(data):
        a,b=number(loc.get('Latitude'),-90,90),number(loc.get('Longitude'),-180,180)
        if a is not None and b is not None:
            d=distance(lat,lon,a,b)
            if d<=max_distance:candidates.append((d,loc))
    return min(candidates,key=lambda p:p[0]) if candidates else None
NUMERIC_FIELDS={'Temperature':('temperature',-60,65),'DewPoint':('dewPoint',-80,65),'ApparentTemperature':('temperatureApparent',-80,85),'MaxTemperature':('temperatureMax',-60,65),'MinTemperature':('temperatureMin',-60,65),'MaxApparentTemperature':('temperatureApparentMax',-80,85),'MinApparentTemperature':('temperatureApparentMin',-80,85),'UVIndex':('uvIndex',0,30)}
DIRECTIONS={'北':0,'北北東':22.5,'東北':45,'東北東':67.5,'東':90,'東南東':112.5,'東南':135,'南南東':157.5,'南':180,'南南西':202.5,'西南':225,'西南西':247.5,'西':270,'西北西':292.5,'西北':315,'北北西':337.5}
def forecast_values(v):
    fields={}
    for src,(dst,lo,hi) in NUMERIC_FIELDS.items():
        n=number(v.get(src),lo,hi)
        if n is not None:fields[dst]=n
    for src,dst,scale in [('RelativeHumidity','humidity',.01),('WindSpeed','windSpeed',3.6),('ProbabilityOfPrecipitation','precipitationChance',.01)]:
        n=number(v.get(src),0,100)
        if n is not None:fields[dst]=n*scale
    wd=v.get('WindDirection','').replace('風','').replace('偏','').strip()
    if wd in DIRECTIONS:fields['windDirection']=DIRECTIONS[wd]
    if v.get('WeatherCode') is not None:
        fields['weatherCode']=str(v['WeatherCode']).zfill(2);fields['weatherText']=v.get('Weather')
    return fields
def normalize_forecast(loc):
    points,intervals={},[]
    for el in loc.get('WeatherElement',loc.get('weatherElement',[])):
        name=el.get('ElementName',el.get('elementName',''))
        for t in el.get('Time',el.get('time',[])):
            vals=t.get('ElementValue',t.get('elementValue',[]));v=vals[0] if vals and isinstance(vals[0],dict) else {};fields=forecast_values(v)
            if not fields:continue
            point=epoch(t.get('DataTime'));start,end=epoch(t.get('StartTime')),epoch(t.get('EndTime'))
            if point is not None:points.setdefault(point,{'forecastStart':point}).update(fields)
            elif start is not None and end is not None and end>start:intervals.append({'start':start,'end':end,'element':name,**fields})
    return {'points':sorted(points.values(),key=lambda p:p['forecastStart']),'intervals':intervals}
