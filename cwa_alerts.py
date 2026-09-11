"""Normalize CWA W-C0033 warning products for the Apple Weather alert root."""
import uuid
from cwa_model import epoch
DETAILS_URL='https://www.cwa.gov.tw/V8/C/W/Warning.html'
ATTRIBUTION_URL='https://opendata.cwa.gov.tw/'

def _areas(record):
    out=[]
    try:
        hazards=record.get('hazardConditions',{}).get('hazards',{}).get('hazard',[])
        if isinstance(hazards,dict):hazards=[hazards]
        for h in hazards:
            locs=h.get('info',{}).get('affectedAreas',{}).get('location',[])
            if isinstance(locs,dict):locs=[locs]
            out.extend(x.get('locationName') for x in locs if x.get('locationName'))
    except (AttributeError,TypeError):pass
    return out

def _phenomenon(record):
    try:
        hs=record.get('hazardConditions',{}).get('hazards',{}).get('hazard',[])
        if isinstance(hs,dict):hs=[hs]
        return next((h.get('info',{}).get('phenomena') for h in hs if h.get('info',{}).get('phenomena')),record.get('datasetInfo',{}).get('datasetDescription','氣象警特報'))
    except (AttributeError,TypeError):return record.get('datasetInfo',{}).get('datasetDescription','氣象警特報')

def _significance(record):
    try:
        hs=record.get('hazardConditions',{}).get('hazards',{}).get('hazard',[])
        if isinstance(hs,dict):hs=[hs]
        text=next((h.get('info',{}).get('significance','') for h in hs if h.get('info')), '')
    except (AttributeError,TypeError):text=''
    return 'WARNING' if '警報' in text else 'ADVISORY' if ('特報' in text or '注意' in text) else 'STATEMENT'

def _severity(text):
    if any(x in text for x in ['超大豪雨','海嘯']):return 'EXTREME'
    if any(x in text for x in ['大豪雨','豪雨','颱風','大雷雨']):return 'SEVERE'
    if any(x in text for x in ['大雨','強風','低溫','高溫','濃霧','長浪','冰雹']):return 'MODERATE'
    return 'MINOR'

def normalize_alerts(detail_data,county,lat,lon,now):
    if not isinstance(detail_data,dict):return {'alerts':[],'reportedTime':int(now)}
    rows=detail_data.get('records',{}).get('record',[])
    if isinstance(rows,dict):rows=[rows]
    alerts=[];reported=[]
    for r in rows:
        if county not in _areas(r):continue
        info=r.get('datasetInfo',{});valid=info.get('validTime',{});start=epoch(valid.get('startTime'));end=epoch(valid.get('endTime'));issued=epoch(info.get('issueTime'))
        if start is None or end is None or end<=now-300 or start>end:continue
        phenomenon=_phenomenon(r);desc=r.get('contents',{}).get('content',{}).get('contentText') or info.get('datasetDescription') or phenomenon
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'CWA|{county}|{phenomenon}|{issued}|{start}|{end}'))
        alerts.append({'id':uid,'areaId':county,'areaName':county,'attributionUrl':ATTRIBUTION_URL,'countryCode':'TW','description':desc.strip(),'token':uid,'effectiveTime':start,'expireTime':end,'issuedTime':issued or start,'eventOnsetTime':start,'eventEndTime':end,'detailsUrl':DETAILS_URL,'phenomenon':phenomenon,'severity':_severity(phenomenon),'significance':_significance(r),'source':'中央氣象署','eventSource':'CWA','urgency':'IMMEDIATE' if start<=now else 'EXPECTED','certainty':'UNKNOWN','importance':'NORMAL','responses':['AVOID'],'unknown23':0,'unknown24':0,'unknown25':0,'unknown26':0})
        reported.append(issued or start)
    return {'alerts':alerts,'reportedTime':max(reported) if reported else int(now),'detailsUrl':DETAILS_URL,'attributionUrl':ATTRIBUTION_URL,'latitude':lat,'longitude':lon}
