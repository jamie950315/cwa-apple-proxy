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
 logger=logging.getLogger('cwa-weather-bridge')
 for h in logger.handlers[:]:h.close();logger.removeHandler(h)
 yield addon.Bridge()
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

def test_translation_handles_compressed_response(bridge):
 import base64,gzip
 snapshot={'source':'CWA','location':{'stationId':'TEST'},'current':{'temperature':20,'observationTime':int(__import__('time').time())}}
 class Client:
  async def get(self,*a,**kw):return httpx.Response(200,request=httpx.Request('GET','http://local'),json=snapshot)
  async def post(self,*a,**kw):return httpx.Response(200,request=httpx.Request('POST','http://local'),json={'body':base64.b64encode(b'modified bytes').decode(),'report':{'modifiedFields':1,'skippedFields':0}})
 bridge.client=Client();f=flow();f.response.encode('gzip')
 asyncio.run(bridge.response(f));assert f.response.content==b'modified bytes';assert gzip.decompress(f.response.raw_content)==b'modified bytes';assert 'etag' not in f.response.headers;assert f.response.headers['x-cwa-bridge'].startswith('0.3.1')


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
