import asyncio,json,time
import httpx,pytest
import cwa_client
from cwa_client import Store,Unavailable

def test_cache_failure_and_key_redaction(tmp_path,monkeypatch):
 monkeypatch.setattr(cwa_client,'ROOT',tmp_path);(tmp_path/'data').mkdir();(tmp_path/'.env').write_text('CWA_API_KEY=test-secret-key')
 async def go():
  s=Store();await s.client.aclose();calls=[]
  def handler(req):calls.append(req);return httpx.Response(200,json={'success':'true','records':{'Station':[]}})
  s.client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
  results=await asyncio.gather(*(s.get('O-A0003-001') for _ in range(20)))
  assert len(calls)==1 and len(results)==20
  stamp,data=s.cache['O-A0003-001'];s.cache['O-A0003-001']=(time.time()-500,data)
  await s.client.aclose();s.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda req:httpx.Response(503)))
  assert await s.get('O-A0003-001')==data
  assert 'test-secret-key' not in json.dumps(s.health())
  s.cache['O-A0003-001']=(time.time()-4000,data)
  with pytest.raises(Unavailable):await s.get('O-A0003-001')
  with pytest.raises(ValueError):await s.get('../../private')
  await s.close()
 asyncio.run(go())

def test_geographic_guard_precedes_download():
 from cwa_snapshot import snapshot
 class NoDownloads:
  async def get(self,_):raise AssertionError('Unexpected download')
 async def go():
  for lat,lon,country in [(35,139,'JP'),(48,12,'AT'),(0,0,'TW')]:
   with pytest.raises(Unavailable):await snapshot(NoDownloads(),lat,lon,country)
  with pytest.raises(ValueError):await snapshot(NoDownloads(),float('nan'),121,'TW')
 asyncio.run(go())
