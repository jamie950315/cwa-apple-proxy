from cwa_alerts import normalize_alerts
from cwa_model import epoch

def fixture():
 return {'records':{'record':[{'datasetInfo':{'datasetDescription':'陸上強風特報','validTime':{'startTime':'2026-09-11 04:28:00','endTime':'2026-09-12 23:00:00'},'issueTime':'2026-09-11 04:29:00'},'contents':{'content':{'contentText':'強風注意事項'}},'hazardConditions':{'hazards':{'hazard':[{'info':{'phenomena':'陸上強風','significance':'特報','affectedAreas':{'location':[{'locationName':'臺北市'},{'locationName':'新北市'}]}}}]}}}]}}
def test_alert_filter_and_mapping():
 now=epoch('2026-09-11T10:00:00+08:00');d=normalize_alerts(fixture(),'臺北市',25.1,121.5,now);assert len(d['alerts'])==1;a=d['alerts'][0];assert a['phenomenon']=='陸上強風';assert a['severity']=='MODERATE';assert a['significance']=='ADVISORY';assert a['source']=='中央氣象署';assert a['eventOnsetTime']<a['eventEndTime'];assert d['detailsUrl'].startswith('https://www.cwa.gov.tw/')
 assert normalize_alerts(fixture(),'高雄市',22.6,120.3,now)['alerts']==[]
