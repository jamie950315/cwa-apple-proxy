import math,time
import pytest
from cwa_model import number,epoch,distance,choose_station,normalize_observation,normalize_forecast
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
@pytest.mark.parametrize('start,end',[('2026-09-11T03:00:00+08:00','2026-09-11T06:00:00+08:00'),('2026-09-11T06:00:00+08:00','2026-09-11T18:00:00+08:00')])
def test_precipitation_interval_preserved(start,end):
 loc={'WeatherElement':[{'ElementName':'降雨機率','Time':[{'StartTime':start,'EndTime':end,'ElementValue':[{'ProbabilityOfPrecipitation':'70'}]}]}]}
 d=normalize_forecast(loc);assert not d['points'];assert len(d['intervals'])==1
 assert math.isclose(d['intervals'][0]['precipitationChance'],.7)
 assert d['intervals'][0]['end']-d['intervals'][0]['start']==epoch(end)-epoch(start)
