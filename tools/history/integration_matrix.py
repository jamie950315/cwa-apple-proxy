import asyncio,json,time,statistics,base64
from pathlib import Path
import httpx
from cwa_model import locations
ROOT=Path('/home/jamie/cwa-weather-proxy')
async def main():
 async with httpx.AsyncClient(timeout=50,trust_env=False) as client:
  national=json.loads((ROOT/'data/F-D0047-091.json').read_text());centers=locations(national);sem=asyncio.Semaphore(4)
  async def city(loc):
   async with sem:
    t=time.monotonic();r=await client.get('http://100.78.140.101:18880/v1/cwa/weather',params={'latitude':loc['Latitude'],'longitude':loc['Longitude'],'country':'TW'});d=r.json()
    return {'county':loc['LocationName'],'http':r.status_code,'milliseconds':round((time.monotonic()-t)*1000),'location':d.get('location'),'temperature':d.get('current',{}).get('temperature'),'hourPoints':len(d.get('shortTerm',{}).get('points',[])),'weeklyIntervals':len(d.get('weekly',{}).get('intervals',[])),'forecastDatasets':d.get('provenance',{}).get('forecastDatasets'),'error':d.get('detail')}
  matrix=await asyncio.gather(*(city(loc) for loc in centers))
  latencies=[]
  async def cached():
   async with sem:
    t=time.monotonic();r=await client.get('http://100.78.140.101:18880/v1/cwa/weather?latitude=25.09&longitude=121.56');r.raise_for_status();latencies.append((time.monotonic()-t)*1000);return r.json()
  snapshots=await asyncio.gather(*(cached() for _ in range(40)))
  source=json.loads((ROOT/'research/actual-brief.json').read_text())['source'];body=base64.b64encode((ROOT/'research'/f'apple-{source["id"]}.bin').read_bytes()).decode()
  codec_times=[]
  async def codec():
   async with sem:
    t=time.monotonic();r=await client.post('http://127.0.0.1:18881/transform',json={'body':body,'snapshot':snapshots[0]});r.raise_for_status();d=r.json();assert d['report']['modifiedFields']>100;codec_times.append((time.monotonic()-t)*1000)
  await asyncio.gather(*(codec() for _ in range(100)))
  def summary(vals):
   v=sorted(vals);return {'requests':len(v),'medianMs':round(statistics.median(v),2),'p95Ms':round(v[int(len(v)*.95)-1],2),'maxMs':round(max(v),2)}
  report={'time':int(time.time()),'countyMatrix':matrix,'normalizedAPI':summary(latencies),'codec':summary(codec_times),'codecFixture':'Captured macOS Taiwan FlatBuffer, replayed locally; these are test requests, not 100 native app refreshes','health':(await client.get('http://100.78.140.101:18880/healthz')).json()}
  (ROOT/'research/integration-matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
  print(json.dumps({'cities':len(matrix),'success':sum(r['http']==200 for r in matrix),'failed':[r for r in matrix if r['http']!=200],'normalizedAPI':report['normalizedAPI'],'codec':report['codec']},ensure_ascii=False))
asyncio.run(main())
