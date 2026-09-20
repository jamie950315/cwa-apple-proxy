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

def test_fresh_cache_does_not_wait_for_proactive_refresh(tmp_path,monkeypatch):
 monkeypatch.setattr(cwa_client,'ROOT',tmp_path);(tmp_path/'data').mkdir();(tmp_path/'.env').write_text('CWA_API_KEY=test-secret-key')
 async def go():
  s=Store();await s.client.aclose();key='O-A0003-001';old={'version':1};s.cache[key]=(time.time()-250,old)
  started=asyncio.Event();release=asyncio.Event()
  async def refresh():started.set();await release.wait();return {'version':2}
  task=asyncio.create_task(s._cached(key,refresh,refresh_ahead=60));await started.wait()
  foreground_called=False
  async def foreground():
   nonlocal foreground_called;foreground_called=True;return {'version':3}
  assert await asyncio.wait_for(s._cached(key,foreground),.1)==old
  assert not foreground_called
  release.set();assert await task=={'version':2}
  await s.close()
 asyncio.run(go())

def test_refresh_due_replaces_active_entry_before_expiry(tmp_path,monkeypatch):
 monkeypatch.setattr(cwa_client,'ROOT',tmp_path);(tmp_path/'data').mkdir();(tmp_path/'.env').write_text('CWA_API_KEY=test-secret-key')
 async def go():
  s=Store();await s.client.aclose();calls=0
  async def fetch():
   nonlocal calls;calls+=1;return {'version':calls}
  assert await s._cached('O-A0003-001',fetch)=={'version':1}
  _,data=s.cache['O-A0003-001'];s.cache['O-A0003-001']=(time.time()-245,data)
  result=await s.refresh_due()
  assert result['O-A0003-001']=={'version':2}
  assert s.cache['O-A0003-001'][1]=={'version':2} and calls==2
  await s.close()
 asyncio.run(go())

def test_proactive_failure_preserves_existing_expiry_and_stale_limits(tmp_path,monkeypatch):
 monkeypatch.setattr(cwa_client,'ROOT',tmp_path);(tmp_path/'data').mkdir();(tmp_path/'.env').write_text('CWA_API_KEY=test-secret-key')
 async def go():
  s=Store();await s.client.aclose();key='O-A0003-001';old={'version':1};calls=0
  async def failing():
   nonlocal calls;calls+=1;raise OSError('temporary failure')
  s.cache[key]=(time.time()-245,old)
  assert await s._cached(key,failing)==old
  result=await s.refresh_due()
  assert result[key]==old and calls==1 and key in s.errors
  stamp,_=s.cache[key];assert time.time()-stamp>=245
  s.cache[key]=(time.time()-301,old)
  assert await s._cached(key,failing)==old and calls==1
  s.cache[key]=(time.time()-4000,old)
  with pytest.raises(Unavailable):await s._cached(key,failing)
  assert calls==1
  await s.close()
 asyncio.run(go())

def test_cold_cache_misses_still_coalesce(tmp_path,monkeypatch):
 monkeypatch.setattr(cwa_client,'ROOT',tmp_path);(tmp_path/'data').mkdir();(tmp_path/'.env').write_text('CWA_API_KEY=test-secret-key')
 async def go():
  s=Store();await s.client.aclose();calls=0
  async def fetch():
   nonlocal calls;calls+=1;await asyncio.sleep(.01);return {'ok':True}
  results=await asyncio.gather(*(s._cached('O-A0003-001',fetch) for _ in range(20)))
  assert results==[{'ok':True}]*20 and calls==1
  await s.close()
 asyncio.run(go())
