import asyncio,logging
from types import SimpleNamespace
import httpx,pytest
from mitmproxy import http
import addon

def flow(country='TW',status=200,content=b'original bytes'):
 return SimpleNamespace(request=http.Request.make('GET','https://weatherkit.apple.com/api/v2/weather/zh-Hant-TW/25.09/121.56?country='+country),response=http.Response.make(status,content,{'Content-Type':'application/vnd.apple.flatbuffer;messageType=WK2.Weather','ETag':'original'}))
@pytest.fixture
def bridge(tmp_path,monkeypatch):
 (tmp_path/'logs').mkdir();(tmp_path/'data').mkdir();monkeypatch.setattr(addon,'ROOT',tmp_path)
 loggers=[logging.getLogger(name) for name in ['cwa-weather-bridge','cwa-weather-transport']]
 for logger in loggers:
  for h in logger.handlers[:]:h.close();logger.removeHandler(h)
 yield addon.Bridge()
 for logger in loggers:
  for h in logger.handlers[:]:h.close();logger.removeHandler(h)
@pytest.mark.parametrize('country',['JP','AT','US',''])
def test_foreign_passthrough(bridge,country):
 f=flow(country);body=f.response.content;headers=f.response.headers.copy()
 asyncio.run(bridge.response(f));assert f.response.content==body;assert f.response.headers==headers;assert bridge.stats['passthrough']==1
@pytest.mark.parametrize('status',[304,401,403,429,500,503])
def test_upstream_status_passthrough(bridge,status):
 f=flow(status=status);asyncio.run(bridge.response(f));assert f.response.content==b'original bytes'
def test_api_failure_preserves_response(bridge):
 class Failed:
  async def get(self,*a,**kw):raise httpx.ConnectError('Simulated failure')
 bridge.client=Failed();f=flow();headers=f.response.headers.copy()
 asyncio.run(bridge.response(f));assert f.response.content==b'original bytes';assert f.response.headers==headers;assert bridge.stats['errors']==1

def test_cache_validators_only_removed_for_target(bridge):
 f=flow();f.request.headers['If-None-Match']='abc';bridge.request(f);assert 'If-None-Match' not in f.request.headers
 f=flow('JP');f.request.headers['If-None-Match']='abc';bridge.request(f);assert f.request.headers['If-None-Match']=='abc'

@pytest.mark.parametrize('failure',['cwa503','codec422','malformed_base64','wrong_length','timeout'])
def test_all_translation_errors_preserve_bytes_and_headers(bridge,failure):
 import base64
 class Client:
  async def get(self,*a,**kw):
   if failure=='timeout':raise TimeoutError('test')
   return httpx.Response(503 if failure=='cwa503' else 200,request=httpx.Request('GET','http://local'),json={'source':'CWA'})
  async def post(self,*a,**kw):
   body='???' if failure=='malformed_base64' else base64.b64encode(b'x').decode()
   return httpx.Response(422 if failure=='codec422' else 200,request=httpx.Request('POST','http://local'),json={'body':body,'report':{'modifiedFields':1}})
 bridge.client=Client();f=flow();headers=f.response.headers.copy();body=f.response.content
 asyncio.run(bridge.response(f));assert f.response.content==body;assert f.response.headers==headers;assert bridge.stats['errors']==1

def test_regular_proxy_rejects_unrelated_connect(bridge):
 f=SimpleNamespace(request=http.Request.make('CONNECT','https://example.org/'),response=None)
 bridge.http_connect(f);assert f.response.status_code==403

def test_transport_diagnostics_redact_sensitive_values(bridge,tmp_path):
 import json
 conn=SimpleNamespace(id='test-connection',sni='weatherkit.apple.com',error='TLS alert unknown ca; private detail')
 bridge.tls_failed_client(SimpleNamespace(conn=conn));bridge.tls_established_client(SimpleNamespace(conn=conn))
 f=flow();f.client_conn=conn;f.request.headers['User-Agent']='WeatherKit_Weather_watchOS_Version test-private';bridge.transport_response(f)
 text=(tmp_path/'logs'/'transport-reverse.jsonl').read_text();events=[json.loads(line) for line in text.splitlines()]
 assert [e['event'] for e in events]==['tls-failed','tls-established','http-response']
 assert events[0]['reason']=='unknown-ca'
 assert events[2]['platform']=='watchos' and events[2]['endpoint']=='weather-v2' and events[2]['status']==200
 assert all(value not in text for value in ['25.09','121.56','private','country','WeatherKit'])
 conn.sni='example.org';bridge.tls_failed_client(SimpleNamespace(conn=conn));bridge.tls_established_client(SimpleNamespace(conn=conn))
 assert (tmp_path/'logs'/'transport-reverse.jsonl').read_text()==text

def test_translation_handles_compressed_response(bridge):
 import base64,gzip
 snapshot={'source':'CWA','location':{'stationId':'TEST'},'current':{'temperature':20,'observationTime':int(__import__('time').time())}}
 class Client:
  async def get(self,*a,**kw):return httpx.Response(200,request=httpx.Request('GET','http://local'),json=snapshot)
  async def post(self,*a,**kw):return httpx.Response(200,request=httpx.Request('POST','http://local'),json={'body':base64.b64encode(b'modified bytes').decode(),'report':{'modifiedFields':1,'skippedFields':0}})
 bridge.client=Client();f=flow();f.response.encode('gzip');f.request.timestamp_end=10;f.response.timestamp_end=10.25
 asyncio.run(bridge.response(f));assert f.response.content==b'modified bytes';assert gzip.decompress(f.response.raw_content)==b'modified bytes';assert 'etag' not in f.response.headers;assert f.response.headers['x-cwa-bridge'].startswith('0.3.2')
 import json
 event=json.loads((addon.ROOT/'data'/'bridge-status.json').read_text())['last']
 assert event['appleResponseMs']==250
 assert all(event[k]>=0 for k in ['cwaMs','codecMs','proofMs','proxyTotalMs'])


def test_deadline_fallback_schedules_ntfy(bridge,monkeypatch):
 captured=[];bridge.notify_failure=lambda reason,event:captured.append((reason,event.copy()))
 class Slow:
  async def get(self,*a,**kw):await asyncio.sleep(.1)
 bridge.client=Slow();monkeypatch.setattr(addon,'DEADLINE',.01);f=flow();body=f.response.content
 asyncio.run(bridge.response(f));assert f.response.content==body;assert captured[0][0]=='timeout-3.5s';assert captured[0][1]['fallbackReason']=='timeout-3.5s'

def test_ntfy_notification_is_throttled_and_has_no_coordinates(bridge):
 sent=[]
 class Reply:
  def raise_for_status(self):pass
 class Ntfy:
  async def post(self,url,content,headers):sent.append((url,content.decode(),headers));return Reply()
 bridge.ntfy=Ntfy();event={'elapsedMs':3501,'latitude':25.1,'longitude':121.5}
 async def go():await bridge._notify('timeout-3.5s',event);await bridge._notify('timeout-3.5s',event)
 asyncio.run(go());assert len(sent)==1;assert sent[0][0]=='https://ntfy.sh/cwa-apple-proxy';assert '25.1' not in sent[0][1] and '121.5' not in sent[0][1]

def test_first_ntfy_notification_is_sent_during_first_five_minutes(bridge,monkeypatch):
 sent=[]
 class Reply:
  def raise_for_status(self):pass
 class Ntfy:
  async def post(self,*args,**kwargs):sent.append(kwargs);return Reply()
 bridge.ntfy=Ntfy();monkeypatch.setattr(addon.time,'monotonic',lambda:10)
 asyncio.run(bridge._notify('timeout-3.5s',{'elapsedMs':3501}));assert len(sent)==1

def test_slow_proof_respects_deadline_and_does_not_block_event_loop(bridge,monkeypatch):
 import base64,json,time
 snapshot={'source':'CWA','location':{'stationId':'TEST'},'current':{'temperature':20,'observationTime':1}}
 class Client:
  async def get(self,*a,**kw):return httpx.Response(200,request=httpx.Request('GET','http://local'),json=snapshot)
  async def post(self,*a,**kw):return httpx.Response(200,request=httpx.Request('POST','http://local'),json={'body':base64.b64encode(b'modified bytes').decode(),'report':{'modifiedFields':1,'skippedFields':0}})
 proof_events=[]
 def slow_proof(*args):proof_events.append(args[-1]);time.sleep(.1);return 'data/proofs/test'
 bridge.client=Client();bridge.proof=slow_proof;captured=[];bridge.notify_failure=lambda reason,event:captured.append(reason)
 monkeypatch.setattr(addon,'DEADLINE',.025);f=flow();body=f.response.raw_content;headers=f.response.headers.copy();ticks=[]
 async def go():
  async def tick():await asyncio.sleep(.005);ticks.append(time.monotonic())
  started=time.monotonic();ticker=asyncio.create_task(tick());await bridge.response(f);elapsed=time.monotonic()-started;await ticker;return started,elapsed
 started,elapsed=asyncio.run(go())
 assert f.response.raw_content==body and f.response.headers==headers
 assert bridge.stats['modified']==0 and bridge.stats['errors']==1
 assert captured==['timeout-3.5s'];assert elapsed<.075;assert ticks[0]-started<.075
 event=json.loads((addon.ROOT/'data/bridge-status.json').read_text())['last']
 assert event['status']=='passthrough'
 assert proof_events[0]['status']=='encoded-candidate' and proof_events[0]['servingOutcomeSource']=='bridge-log'
 assert proof_events[0]['requestId']==event['requestId']

def test_proof_timeout_does_not_queue_another_disk_worker(bridge):
 import threading
 started=threading.Event();release=threading.Event();calls=[]
 def slow_proof(*args):calls.append(args);started.set();release.wait(1);return 'data/proofs/test'
 bridge.proof=slow_proof
 async def go():
  first=asyncio.create_task(bridge.proof_async(b'original',b'mapped',{}, {},{}))
  try:
   assert await asyncio.to_thread(started.wait,1)
   with pytest.raises(TimeoutError):
    async with asyncio.timeout(.01):await bridge.proof_async(b'other',b'other',{}, {},{})
   assert len(calls)==1 and not first.done()
  finally:release.set()
  assert await first=='data/proofs/test'
 asyncio.run(go());assert len(calls)==1

def test_proof_worker_error_is_observed_after_response_timeout(bridge):
 import gc,threading
 started=threading.Event();release=threading.Event();errors=[]
 def failed_proof(*args):started.set();release.wait(1);raise OSError('simulated proof failure')
 bridge.proof=failed_proof
 async def go():
  asyncio.get_running_loop().set_exception_handler(lambda loop,context:errors.append(context))
  waiting=asyncio.create_task(bridge.proof_async(b'original',b'mapped',{}, {},{}))
  try:
   assert await asyncio.to_thread(started.wait,1)
   with pytest.raises(TimeoutError):
    async with asyncio.timeout(.01):await waiting
  finally:release.set()
  await asyncio.wait({bridge.proof_task})
  bridge.proof_task=None;gc.collect();await asyncio.sleep(0)
 asyncio.run(go());assert errors==[]
