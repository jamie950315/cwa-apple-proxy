import asyncio,json,time
from datetime import datetime,timezone,timedelta
import httpx,pytest
import cwa_client
from cwa_client import Store
from cwa_aqi import normalize_aqi
from cwa_astronomy import normalize_astronomy
from cwa_nwp import normalize_nwp

def test_aqi_index_units_location_and_freshness():
    now=int(time.time());date=datetime.fromtimestamp(now,timezone(timedelta(hours=8))).strftime('%Y/%m/%d %H:%M:%S')
    raw={'data':{'aqi':[{'sitename':'test','siteid':'1','aqi':'44','pollutant':'PM2.5','latitude':'25','longitude':'121','publishtime':date,'co':'0.31','pm2_5':'8','so2':'-99'}]}}
    result=normalize_aqi(raw,25,121,now)
    assert result['index']==44 and result['categoryIndex']==1 and result['scale']=='TAIWAN_AQI'
    assert next(p for p in result['pollutants'] if p['pollutantType']=='CO')['amount']==310
    assert all(p['pollutantType']!='SO2' for p in result['pollutants'])
    assert normalize_aqi(raw,22,120,now) is None
    assert normalize_aqi(raw,25,121,now+5500) is None
    assert normalize_aqi({'errors':[{}],**raw},25,121,now) is None

def test_astronomy_is_calendar_local_and_missing_moon_event_stays_missing():
    sun={'records':{'locations':{'location':[{'CountyName':'臺北市','time':[{'Date':'2026-09-11','SunRiseTime':'05:38','SunSetTime':'18:02'}]}]}}}
    moon={'records':{'locations':{'location':[{'CountyName':'臺北市','time':[{'Date':'2026-09-11','MoonRiseTime':'','MoonSetTime':'18:01'}]}]}}}
    day=normalize_astronomy(sun,moon,'臺北市')['days'][0]
    assert datetime.fromtimestamp(day['sunrise'],timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')=='2026-09-11 05:38'
    assert 'moonrise' not in day and 'moonset' in day
    assert normalize_astronomy(sun,moon,'臺南市')['days']==[]

def model_product(values,cycles=None):
    initial=1_789_000_000
    rows=[{'initialTime':initial if cycles is None else cycles[i],'forecastTime':initial+(i+1)*21600,'leadHours':(i+1)*6,'values':[v],'geometry':'g'} for i,v in enumerate(values)]
    return {'version':1,'generatedAt':initial+1000,'towns':[{'county':'臺北市','town':'信義區'}],'fields':{'apcp':rows,'pressure':[]},'geometry':{'g':[{'distanceKm':1}]}},initial

def test_nwp_accumulations_same_run_difference_and_missing_intervals():
    product,initial=model_product([1,3,4])
    result=normalize_nwp(product,'臺北市','信義區',initial+1000)
    assert [r['amount'] for r in result['rainIntervals']]==[1,2,1]
    assert normalize_nwp(product,'臺北市','信義區',initial+86401) is None
    product,initial=model_product([1,None,4,6]);r=normalize_nwp(product,'臺北市','信義區',initial+1000)
    assert [r['amount'] for r in r['rainIntervals']]==[1,2]
    product,initial=model_product([2,1]);r=normalize_nwp(product,'臺北市','信義區',initial+1000)
    assert len(r['rainIntervals'])==1

def test_nwp_never_differences_different_initializations():
    product,initial=model_product([1,10],cycles=[1_789_000_000,1_789_000_100])
    r=normalize_nwp(product,'臺北市','信義區',initial+1000)
    assert r['initialTime']==initial+100 and r['rainIntervals']==[]

def test_store_astronomy_explicit_window_and_linked_aqi_auth(tmp_path,monkeypatch):
    monkeypatch.setattr(cwa_client,'ROOT',tmp_path);(tmp_path/'data').mkdir();(tmp_path/'.env').write_text('CWA_API_KEY=unit-test-secret')
    seen=[]
    def handle(req):
        seen.append(req)
        if req.url.path.endswith('/linked/graphql'):
            assert req.headers['Authorization']=='unit-test-secret'
            assert 'unit-test-secret' not in str(req.url)
            return httpx.Response(200,json={'data':{'aqi':[{'aqi':'44'}]}})
        today=datetime.now(timezone(timedelta(hours=8))).date()
        assert req.url.params['timeFrom']==str(today-timedelta(days=1))
        assert req.url.params['timeTo']==str(today+timedelta(days=15))
        return httpx.Response(200,json={'success':'true','records':{'locations':{'location':[]}}})
    async def go():
        store=Store();await store.client.aclose();store.client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        await store.get('A-B0062-001');await store.linked_aqi();await store.linked_aqi()
        assert len(seen)==2 and 'unit-test-secret' not in json.dumps(store.health())
        await store.close()
    asyncio.run(go())
