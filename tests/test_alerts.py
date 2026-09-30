from cwa_alerts import normalize_alerts
from cwa_model import epoch

def fixture():
 return {'records':{'record':[{'datasetInfo':{'datasetDescription':'陸上強風特報','validTime':{'startTime':'2026-09-11 04:28:00','endTime':'2026-09-12 23:00:00'},'issueTime':'2026-09-11 04:29:00'},'contents':{'content':{'contentText':'強風注意事項'}},'hazardConditions':{'hazards':{'hazard':[{'info':{'phenomena':'陸上強風','significance':'特報','affectedAreas':{'location':[{'locationName':'臺北市'},{'locationName':'新北市'}]}}}]}}}]}}
def test_alert_filter_and_mapping():
 now=epoch('2026-09-11T10:00:00+08:00');d=normalize_alerts(fixture(),'臺北市',25.1,121.5,now);assert len(d['alerts'])==1;a=d['alerts'][0];assert a['phenomenon']=='陸上強風';assert a['severity']=='MODERATE';assert a['significance']=='ADVISORY';assert a['source']=='中央氣象署';assert a['eventOnsetTime']<a['eventEndTime'];assert d['detailsUrl'].startswith('https://www.cwa.gov.tw/')
 assert normalize_alerts(fixture(),'高雄市',22.6,120.3,now)['alerts']==[]

def test_alert_hazard_and_significance_follow_its_own_affected_county():
 data=fixture();record=data['records']['record'][0]
 record['hazardConditions']['hazards']['hazard']=[
  {'info':{'phenomena':'豪雨','significance':'警報','affectedAreas':{'location':[{'locationName':'高雄市'}]}}},
  {'info':{'phenomena':'大雨','significance':'特報','affectedAreas':{'location':[{'locationName':'台北市'}]}}},
  {'info':{'phenomena':'強風','significance':'注意','affectedAreas':{'location':[{'locationName':'臺北市'}]}}},
 ]
 now=epoch('2026-09-11T10:00:00+08:00')
 alerts=normalize_alerts(data,'臺北市',25.1,121.5,now)['alerts']
 assert [(a['phenomenon'],a['severity'],a['significance']) for a in alerts]==[('大雨','MODERATE','ADVISORY'),('強風','MODERATE','ADVISORY')]
 assert len({a['id'] for a in alerts})==2
 kaohsiung=normalize_alerts(data,'高雄市',22.6,120.3,now)['alerts']
 assert [(a['phenomenon'],a['severity'],a['significance']) for a in kaohsiung]==[('豪雨','SEVERE','WARNING')]

def test_alert_duplicate_hazards_have_one_stable_identity_and_reject_empty_window():
 data=fixture();record=data['records']['record'][0];hazards=record['hazardConditions']['hazards']['hazard']
 hazards.append(hazards[0])
 now=epoch('2026-09-11T10:00:00+08:00')
 alerts=normalize_alerts(data,'臺北市',25.1,121.5,now)['alerts']
 assert len(alerts)==1
 assert normalize_alerts(data,'臺北市',25.1,121.5,now+1)['alerts'][0]['id']==alerts[0]['id']
 valid=record['datasetInfo']['validTime'];valid['startTime']=valid['endTime']
 assert normalize_alerts(data,'臺北市',25.1,121.5,now)['alerts']==[]
