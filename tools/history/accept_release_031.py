"""Read-only release acceptance: live CWA towns, codec replay, and native proof."""
import asyncio,base64,datetime,json,math,statistics,time
from pathlib import Path
import httpx
ROOT=Path('/home/jamie/cwa-weather-proxy')
async def main():
 gate=json.loads((ROOT/'reports/release-gate-latest.json').read_text())
 if gate.get('status')!='passed':raise RuntimeError('Release gate has not passed; acceptance stopped')
 report={'version':'0.3.1','startedAt':datetime.datetime.now().astimezone().isoformat(),'nativeUI':'Visual verification is separately required; server-side proof alone does not establish every UI panel.'}
 towns=json.loads((ROOT/'town_index.json').read_text());sem=asyncio.Semaphore(4)
 async with httpx.AsyncClient(timeout=httpx.Timeout(40,connect=5),trust_env=False) as c:
  async def town(t):
   async with sem:
    start=time.monotonic()
    try:
     r=await c.get('http://100.78.140.101:18880/v1/cwa/weather',params={'latitude':t['latitude'],'longitude':t['longitude'],'country':'TW'});r.raise_for_status();d=r.json()
     assert math.isfinite(d['current']['temperature']) and d['shortTerm']['points']
     return {'county':t['county'],'town':t['town'],'passed':True,'elapsedMs':round((time.monotonic()-start)*1000),'rain':bool(d.get('rain')),'aqi':bool(d.get('airQuality')),'nwp':bool(d.get('nwp')),'astronomy':bool((d.get('astronomy') or {}).get('days'))}
    except Exception as e:return {'county':t.get('county'),'town':t.get('town'),'passed':False,'error':type(e).__name__}
  rows=await asyncio.gather(*(town(t) for t in towns))
  report['towns']={'count':len(rows),'passed':sum(x['passed'] for x in rows),'failures':[x for x in rows if not x['passed']],'optionalCoverage':{k:sum(bool(x.get(k)) for x in rows) for k in ['rain','aqi','nwp','astronomy']}}
  (ROOT/'reports/acceptance-031-towns.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
  fixture=json.loads((ROOT/'research/actual-brief.json').read_text())['source']
  original=(ROOT/'research'/('apple-'+fixture['id']+'.bin')).read_bytes()
  r=await c.get('http://100.78.140.101:18880/v1/cwa/weather?latitude=25.09&longitude=121.56&country=TW');r.raise_for_status();snapshot=r.json()
  payload={'body':base64.b64encode(original).decode(),'snapshot':snapshot}
  latencies=[];failures=[]
  async def replay(i):
   async with sem:
    start=time.monotonic()
    try:
     r=await c.post('http://127.0.0.1:18881/transform',json=payload);r.raise_for_status();d=r.json();body=base64.b64decode(d['body'],validate=True)
     assert 12<=len(body)<=4000000 and d['report']['version']=='0.3.1' and d['report']['modifiedFields']>100
     if i==0:
      (ROOT/'reports/acceptance-031-mapped.bin').write_bytes(body)
      (ROOT/'reports/acceptance-031-snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False))
      report['exampleMapping']=d['report']
     latencies.append((time.monotonic()-start)*1000)
    except Exception as e:failures.append({'request':i,'error':type(e).__name__})
  await asyncio.gather(*(replay(i) for i in range(1000)))
  v=sorted(latencies)
  report['replay']={'requests':1000,'passed':len(v),'failures':failures,'medianMs':round(statistics.median(v),2) if v else None,'p95Ms':round(v[max(0,math.ceil(len(v)*.95)-1)],2) if v else None,'meaning':'Local replay of a captured macOS FlatBuffer; separate from actual native app requests.'}
  report['health']=(await c.get('http://100.78.140.101:18880/healthz')).json()
  report['status']=(await c.get('http://100.78.140.101:18880/status')).json()
  report['passed']=report['towns']['passed']==len(rows) and len(v)==1000
  report['finishedAt']=datetime.datetime.now().astimezone().isoformat()
  (ROOT/'reports/acceptance-031.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
  print(json.dumps({'passed':report['passed'],'towns':report['towns'],'replay':report['replay']},ensure_ascii=False))
  if not report['passed']:raise RuntimeError('Acceptance failures: see reports/acceptance-031.json')
asyncio.run(main())
