import asyncio

import cwa_snapshot
from cwa_model import dewpoint_c,epoch


class FakeStore:
    def __init__(self,station):
        self.station=station

    async def get(self,dataset):
        if dataset=='O-A0001-001':
            return {'records':{'Station':[self.station]}}
        return {}

    async def file_get(self,dataset):
        return {}

    async def linked_aqi(self):
        return {}

    def model_product(self):
        return None


def test_snapshot_keeps_station_thermodynamic_bundle_and_grid_in_provenance(monkeypatch):
    now=epoch('2026-09-20T14:00:00+08:00');observation=now-60
    station={
        'StationId':'C0TEST','StationName':'Test station','ObsTime':{'DateTime':'2026-09-20T13:59:00+08:00'},
        'GeoInfo':{'CountyName':'宜蘭縣','TownName':'宜蘭市','StationAltitude':'10','Coordinates':[{'CoordinateName':'WGS84','StationLatitude':24.73,'StationLongitude':121.745083}]},
        'WeatherElement':{
            'AirTemperature':'30','RelativeHumidity':'50','WindSpeed':'2','WindDirection':'90',
            'DailyExtreme':{
                'DailyHigh':{'TemperatureInfo':{'AirTemperature':'31','Occurred_at':{'DateTime':'2026-09-20T13:30:00+08:00'}}},
                'DailyLow':{'TemperatureInfo':{'AirTemperature':'25','Occurred_at':{'DateTime':'2026-09-20T05:00:00+08:00'}}},
            },
        },
    }
    analysis={'temperature':20.0,'time':now,'gridLatitudeTWD67':24.75,'gridLongitudeTWD67':121.74,'gridDistanceKm':0.1,'source':'CWA O-A0038-003 hourly analyzed temperature grid'}
    monkeypatch.setattr(cwa_snapshot.time,'time',lambda:now)
    monkeypatch.setattr(cwa_snapshot,'temperature_analysis',lambda *args,**kwargs:dict(analysis))
    result=asyncio.run(cwa_snapshot.snapshot(FakeStore(station),24.753707,121.745083))

    assert result['current']['observationTime']==observation
    assert result['current']['temperature']==30.0 and result['current']['humidity']==0.5
    assert result['current']['dewPoint']==dewpoint_c(30.0,0.5)
    assert result['current']['_sources']['temperature']=='CWA station observation'
    assert result['provenance']['temperatureAnalysis']=={**analysis,'usedForCurrent':False}
    assert result['dailyObservedExtremes']['temperatureMin']==25.0
    assert result['dailyObservedExtremes']['temperatureMax']==31.0
    assert result['dailyObservedExtremes']['observationTime']==observation

    del station['WeatherElement']['DailyExtreme']['DailyLow']['TemperatureInfo']['AirTemperature']
    incomplete=asyncio.run(cwa_snapshot.snapshot(FakeStore(station),24.753707,121.745083))
    assert 'dailyObservedExtremes' not in incomplete
