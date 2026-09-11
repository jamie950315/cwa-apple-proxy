from pathlib import Path
import ssl
ctx=ssl.create_default_context(); ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
import urllib.request, urllib.parse, json, concurrent.futures, time
base=Path('/home/jamie/cwa-weather-proxy')
key=dict(line.strip().split('=',1) for line in (base/'.env').read_text().splitlines() if '=' in line)['CWA_API_KEY']
def fetch(dataset):
    url='https://opendata.cwa.gov.tw/api/v1/rest/datastore/'+dataset+'?'+urllib.parse.urlencode({'Authorization':key,'format':'JSON'})
    try:
        with urllib.request.urlopen(url,timeout=45,context=ctx) as r: raw=r.read(); status=r.status
        (base/'data'/f'{dataset}.json').write_bytes(raw)
        d=json.loads(raw)
        rec=d.get('records',{})
        if isinstance(rec,dict):
            overview={k:(len(v) if isinstance(v,list) else str(v)[:200]) for k,v in rec.items()}
            sample=next((v[0] for v in rec.values() if isinstance(v,list) and v), rec)
            if isinstance(sample,dict) and 'Location' in sample: sample={**sample,'Location':sample['Location'][:1]}
            if isinstance(sample,dict) and 'location' in sample: sample={**sample,'location':sample['location'][:1]}
        else: overview=str(rec)[:200];sample=rec
        return {'dataset':dataset,'http':status,'bytes':len(raw),'success':d.get('success'),'overview':overview,'sample':sample}
    except Exception as e:
        return {'dataset':dataset,'errorType':type(e).__name__,'http':getattr(e,'code',None)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(fetch,['O-A0003-001','O-A0001-001','F-D0047-061','F-D0047-063','F-D0047-091','F-D0047-089']))
(base/'research'/'cwa-samples-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print([(x['dataset'],x.get('http'),x.get('bytes')) for x in results])
