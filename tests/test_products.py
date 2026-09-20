import time,math
from cwa_products import temperature_analysis,qpf_next_hour
from cwa_model import normalize_rain,dewpoint_c,visibility_meters

def station():
 return {'GeoInfo':{'Coordinates':[{'CoordinateName':'WGS84','StationLatitude':'25','StationLongitude':'121'},{'CoordinateName':'TWD67','StationLatitude':'25','StationLongitude':'121'}]}}

def test_temperature_grid_sampling():
 now=time.time();ts=__import__('datetime').datetime.fromtimestamp(now,__import__('datetime').timezone.utc).isoformat()
 p={'cwaopendata':{'dataset':{'DataTime':{'DateTime':ts},'GeoInfo':{'BottomLeftLongitude':'121','BottomLeftLatitude':'25','TopRightLongitude':'121.03','TopRightLatitude':'25.03'},'Resource':{'Content':'20,21,22,23'}}}}
 r=temperature_analysis(p,25.03,121.03,station(),now);assert r['temperature']==23

def test_qpf_grid_sampling():
 from datetime import datetime,timezone
 now=time.time();ts=datetime.fromtimestamp(now,timezone.utc).isoformat()
 p={'cwaopendata':{'dataset':{'datasetInfo':{'parameterSet':{'DateTime':ts,'GridDimensionX':'2','GridDimensionY':'2','GridResolution':'0.01','StartPointLongitude':'121','StartPointLatitude':'25'}},'contents':{'content':'0.1,0.2,0.3,4.5'}}}}
 r=qpf_next_hour(p,25.01,121.01,station(),now);assert r['amount']==4.5;assert r['end']-r['start']==3600

def test_rain_and_visibility_derivations():
 s={'RainfallElement':{'Past10Min':{'Precipitation':'0.5'},'Past1hr':{'Precipitation':'T'},'Past6Hr':{'Precipitation':'2.0'},'Past24hr':{'Precipitation':'3.5'}}}
 r=normalize_rain(s,1);assert 'intensity' not in r;assert 'past1h' not in r;assert r['traceFields']==['past1h'];assert r['past24h']==3.5
 assert visibility_meters('11-15')==13000;assert visibility_meters('>30')==30000
 assert 20<dewpoint_c(27,.75)<25
