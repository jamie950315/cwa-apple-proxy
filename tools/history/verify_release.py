"""Live normalized API matrix and replay load test; no Apple authentication tokens stored."""
import asyncio,json,time,statistics,base64,subprocess
from pathlib import Path
import httpx
ROOT=Path('/home/jamie/cwa-weather-proxy')
async def main():
 out={'version':'0.2.0','startedAt':int(time.time()),'testType':'CWA API and captured-body replay; native app proof recorded separately'}
 async with httpx.AsyncClient(timeout=45,trust_env=False) as c:
  towns=json.loads((ROOT/'town_index.json').read_text());sem=asyncio.Semaphore(4)
  async def place(t):
   async with sem:
    started=time.monotonic()
    r=await c.get('http://100.78.140.101:18880/v1/cwa/weather',params={'latitude':t['latitude'],'longitude':t['longitude']});d=r.json()
    return {'county':t['county'],'town':t['town'],'http':r.status_code,'ms':round((time.monotonic()-started)*1000,2),'selected':d.get('location'),'points':len(d.get('shortTerm',{}).get('points',[])),'weekly':len(d.get('weekly',{}).get('intervals',[])),'detail':d.get('detail')}
  matrix=await asyncio.gather(*(place(t) for t in towns))
  out['townMatrix']={'total':len(matrix),'http200':sum(t['http']==200 for t in matrix),'hasShortForecast':sum(t['points']>0 for t in matrix),'hasWeeklyForecast':sum(t['weekly']>0 for t in matrix),'unavailable':[t for t in matrix if t['http']!=200]}
  (ROOT/'research/town-matrix-v2.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2))
  r=await c.get('http://100.78.140.101:18880/v1/cwa/weather?latitude=25.09&longitude=121.56');r.raise_for_status();snapshot=r.json()
  source=json.loads((ROOT/'research/actual-brief.json').read_text())['source'];raw=(ROOT/'research'/f'apple-{source["id"]}.bin').read_bytes();body=base64.b64encode(raw).decode()
  times=[];failures=[]
  async def replay(i):
   async with sem:
    start=time.monotonic()
    try:
     r=await c.post('http://127.0.0.1:18881/transform',json={'body':body,'snapshot':snapshot});r.raise_for_status();d=r.json()
     assert len(base64.b64decode(d['body']))==len(raw)
     assert d['report']['version']=='0.2.0' and d['report']['modifiedFields']>0
     times.append((time.monotonic()-start)*1000)
    except Exception as e:failures.append({'index':i,'error':type(e).__name__})
  await asyncio.gather(*(replay(i) for i in range(1000)))
  times.sort();out['codecReplay']={'requested':1000,'passed':len(times),'failures':failures,'medianMs':round(statistics.median(times),2),'p95Ms':round(times[int(len(times)*.95)-1],2),'maxMs':round(max(times),2)}
  out['httpChecks']={}
  for path in ['/','/healthz','/status','/CWA-Weather.mobileconfig','/ca.cer','/proxy.pac','/v1/cwa/weather?latitude=91&longitude=121','/v1/cwa/weather?latitude=35&longitude=139&country=JP']:
   r=await c.get('http://100.78.140.101:18880'+path);out['httpChecks'][path]={'http':r.status_code,'bytes':len(r.content),'type':r.headers.get('content-type')}
  out['status']=(await c.get('http://100.78.140.101:18880/status')).json()
  # Keep the summary compact while retaining live source comparisons.
  last=out['status'].get('lastProof',{})
  out['nativeProof']={'request':last.get('request'),'currentChanges':[v for v in last.get('report',{}).get('changes',[]) if v['field'].startswith('current.')],'coverage':last.get('report',{}).get('coverage'),'cwaLocation':last.get('cwa',{}).get('location')}
  out['status'].pop('lastProof',None)
  out['serviceStatus']=subprocess.check_output(['systemctl','is-active','cwa-weather-api','cwa-weather-codec','cwa-weather-proxy','cwa-weather-forward','cwa-weather-sni','cwa-weather-routing'],text=True).splitlines()
  out['finishedAt']=int(time.time())
  (ROOT/'research/release-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
  print(json.dumps({k:out[k] for k in ['townMatrix','codecReplay','httpChecks','nativeProof','serviceStatus']},ensure_ascii=False,indent=2))
asyncio.run(main())
