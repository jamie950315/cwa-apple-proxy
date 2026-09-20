import math,time
import pytest
from cwa_model import number,epoch,distance,choose_station,choose_rain_station,normalize_observation,normalize_rain,normalize_daily_extremes,normalize_forecast
@pytest.mark.parametrize('value',['-99',-999,'NaN','inf','X','',None])
def test_missing(value):assert number(value,0,100) is None
@pytest.mark.parametrize('value',[0,'0',10.2,'99.5',100])
def test_valid(value):assert number(value,0,100)==float(value)
def test_timezone():assert epoch('2026-09-11T03:00:00+08:00')==epoch('2026-09-10T19:00:00Z')
def test_distance():assert distance(25,121,25,121)==0;assert 110<distance(24,121,25,121)<112
def station(ts,temp='25',lat=25,lon=121):
 from datetime import datetime,timezone
 return {'ObsTime':{'DateTime':datetime.fromtimestamp(ts,timezone.utc).isoformat()},'GeoInfo':{'Coordinates':[{'CoordinateName':'WGS84','StationLatitude':lat,'StationLongitude':lon}]},'WeatherElement':{'AirTemperature':temp,'RelativeHumidity':'85','WindSpeed':'2.5','WindDirection':'90','UVIndex':'-99','Weather':'-99'}}
def test_station_validation():
 now=time.time();good=station(now-600)
 assert choose_station([station(now-6000),station(now,'-99'),good],25,121)[1] is good
 assert choose_station([good],23,120) is None
 assert choose_station([station(now+1000)],25,121) is None
 d=normalize_observation(good,int(now-600));assert d['humidity']==.85;assert d['windSpeed']==9;assert 'uvIndex' not in d;assert 'weatherText' not in d
def test_rain_trace_is_explicit_and_not_fabricated():
 now=time.time();s=station(now-60);s['RainfallElement']={'Past10Min':{'Precipitation':'T'},'Past1hr':{'Precipitation':' T '},'Past24hr':{'Precipitation':'3.5'}}
 assert choose_rain_station([s],25,121,now=now)[1] is s
 rain=normalize_rain(s,int(now-60))
 assert rain['traceFields']==['past10m','past1h'] and rain['past24h']==3.5
 assert 'past10m' not in rain and 'past1h' not in rain and 'intensity' not in rain
def test_daily_extremes_require_complete_consistent_local_day():
 now=epoch('2026-09-20T14:00:00+08:00');s=station(now-60,temp='27');s['StationId']='46692'
 s['WeatherElement']['DailyExtreme']={
  'DailyHigh':{'TemperatureInfo':{'AirTemperature':'31','Occurred_at':{'DateTime':'2026-09-20T13:30:00+08:00'}}},
  'DailyLow':{'TemperatureInfo':{'AirTemperature':'22','Occurred_at':{'DateTime':'2026-09-20T05:20:00+08:00'}}}}
 result=normalize_daily_extremes(s,now-60,27,now)
 assert result=={'date':'2026-09-20','start':epoch('2026-09-20T00:00:00+08:00'),'end':epoch('2026-09-21T00:00:00+08:00'),'observationTime':now-60,'temperatureMax':31.0,'temperatureMin':22.0,'temperatureMaxTime':epoch('2026-09-20T13:30:00+08:00'),'temperatureMinTime':epoch('2026-09-20T05:20:00+08:00'),'source':'CWA station DailyExtreme observation','stationId':'46692'}
 s['WeatherElement']['DailyExtreme']['DailyHigh']['TemperatureInfo']['Occurred_at']['DateTime']='2026-09-20T14:01:00+08:00'
 assert normalize_daily_extremes(s,now-60,27,now) is None
 s['WeatherElement']['DailyExtreme']['DailyHigh']['TemperatureInfo']['Occurred_at']['DateTime']='2026-09-20T13:30:00+08:00'
 assert normalize_daily_extremes(s,now-60,32,now) is None
 assert normalize_daily_extremes(s,now-60,22,now)['temperatureMin']==22.0
 assert normalize_daily_extremes(s,now-60,31,now)['temperatureMax']==31.0
 assert normalize_daily_extremes(s,now-6000,27,now) is None
 del s['WeatherElement']['DailyExtreme']['DailyLow']['TemperatureInfo']['AirTemperature']
 assert normalize_daily_extremes(s,now-60,27,now) is None
@pytest.mark.parametrize('start,end',[('2026-09-11T03:00:00+08:00','2026-09-11T06:00:00+08:00'),('2026-09-11T06:00:00+08:00','2026-09-11T18:00:00+08:00')])
def test_precipitation_interval_preserved(start,end):
 loc={'WeatherElement':[{'ElementName':'降雨機率','Time':[{'StartTime':start,'EndTime':end,'ElementValue':[{'ProbabilityOfPrecipitation':'70'}]}]}]}
 d=normalize_forecast(loc);assert not d['points'];assert len(d['intervals'])==1
 assert math.isclose(d['intervals'][0]['precipitationChance'],.7)
 assert d['intervals'][0]['end']-d['intervals'][0]['start']==epoch(end)-epoch(start)
