"""WeatherKit-only CWA bridge. Transformation failures immediately return Apple's original response and alert via ntfy."""
from pathlib import Path
import os,asyncio,base64,json,logging,logging.handlers,re,time,uuid
import httpx
from mitmproxy import http
ROOT=Path('/home/jamie/cwa-weather-proxy')
VERSION='0.3.1';MODE=os.getenv('CWA_PROXY_MODE','reverse');DEADLINE=3.5;NTFY_URL='https://ntfy.sh/cwa-apple-proxy'
PATH=re.compile(r'^/api/v2/weather/[^/]+/(-?\d+(?:\.\d+)?)/(-?\d+(?:\.\d+)?)/?$')
class Bridge:
    def __init__(self):
        self.client=None;self.ntfy=None;self.started=int(time.time());self.notify_tasks=set();self.last_notify={}
        self.stats={'seen':0,'modified':0,'unchanged':0,'passthrough':0,'errors':0,'notifications':0,'notificationErrors':0}
        self.log=logging.getLogger('cwa-weather-bridge');self.log.setLevel(logging.INFO)
        if not self.log.handlers:
            handler=logging.handlers.RotatingFileHandler(ROOT/'logs'/f'bridge-{MODE}.jsonl',maxBytes=5000000,backupCount=2,delay=True);handler.setFormatter(logging.Formatter('%(message)s'));self.log.addHandler(handler)
        self.transport_log=logging.getLogger('cwa-weather-transport');self.transport_log.setLevel(logging.INFO);self.transport_log.propagate=False
        if not self.transport_log.handlers:
            handler=logging.handlers.RotatingFileHandler(ROOT/'logs'/f'transport-{MODE}.jsonl',maxBytes=500000,backupCount=2,delay=True);handler.setFormatter(logging.Formatter('%(message)s'));self.transport_log.addHandler(handler)
    def transport_event(self,event,conn,**fields):
        # No URLs, coordinates, headers, raw errors, or TLS secrets belong here.
        try:self.transport_log.info(json.dumps({'time':int(time.time()),'event':event,'connection':str(conn.id) if conn else None,**fields}))
        except OSError:pass
    def tls_established_client(self,data):
        if data.conn.sni=='weatherkit.apple.com':self.transport_event('tls-established',data.conn)
    def tls_failed_client(self,data):
        if data.conn.sni!='weatherkit.apple.com':return
        error=(data.conn.error or '').lower()
        reason=next((name for token,name in [('unknown ca','unknown-ca'),('certificate unknown','certificate-unknown'),('bad certificate','bad-certificate'),('does not trust','certificate-untrusted')] if token in error),'other-tls-failure')
        self.transport_event('tls-failed',data.conn,reason=reason)
    def transport_response(self,flow):
        agent=flow.request.headers.get('user-agent','').lower()
        platform=next((name for name in ['watchos','ios','macos'] if name in agent),'other')
        path=flow.request.path.split('?',1)[0]
        endpoint=next((name for prefix,name in [('/api/v2/weather/','weather-v2'),('/api/v1/weather/','weather-v1'),('/api/v1/airQualityScale/','air-quality-scale')] if path.startswith(prefix)),'other')
        self.transport_event('http-response',getattr(flow,'client_conn',None),platform=platform,endpoint=endpoint,status=flow.response.status_code)
    def running(self):
        # The outer 3.5 second budget governs the whole CWA + codec path.
        self.client=httpx.AsyncClient(timeout=httpx.Timeout(10,connect=1.5),trust_env=False)
        self.ntfy=httpx.AsyncClient(timeout=httpx.Timeout(3,connect=1.5),trust_env=False)
    def http_connect(self,flow):
        if flow.request.host!='weatherkit.apple.com' or flow.request.port!=443:flow.response=http.Response.make(403,b'Weather-only proxy')
    def target(self,flow):
        if flow.request.host!='weatherkit.apple.com' or flow.request.method!='GET':return None
        match=PATH.fullmatch(flow.request.path.split('?',1)[0])
        if not match or flow.request.query.get('country','').upper()!='TW':return None
        lat,lon=map(float,match.groups());return (lat,lon) if 20<=lat<=27 and 117<=lon<=124 else None
    def request(self,flow):
        if flow.request.host!='weatherkit.apple.com':flow.response=http.Response.make(403,b'Weather-only proxy');return
        if self.target(flow):
            for name in ['If-None-Match','If-Modified-Since']:flow.request.headers.pop(name,None)
    def record(self,event):
        try:
            self.log.info(json.dumps(event,ensure_ascii=False));temp=ROOT/'data'/('bridge-status-'+uuid.uuid4().hex+'.tmp')
            temp.write_text(json.dumps({'version':VERSION,'startedAt':self.started,'deadlineSeconds':DEADLINE,'ntfyTopic':'cwa-apple-proxy','stats':self.stats,'last':event},ensure_ascii=False));temp.replace(ROOT/'data'/('bridge-status-forward.json' if MODE=='forward' else 'bridge-status.json'))
        except OSError:pass
    def proof(self,original,body,snapshot,report,event):
        folder=ROOT/'data/proofs'/str(uuid.uuid4());folder.mkdir(parents=True,exist_ok=True)
        (folder/'original.bin').write_bytes(original);(folder/'mapped.bin').write_bytes(body);(folder/'cwa.json').write_text(json.dumps(snapshot,ensure_ascii=False));(folder/'report.json').write_text(json.dumps(report,ensure_ascii=False));(folder/'request.json').write_text(json.dumps(event,ensure_ascii=False))
        old=sorted((ROOT/'data/proofs').iterdir(),key=lambda p:p.stat().st_mtime)
        for d in old[:-20]:
            for f in d.iterdir():f.unlink()
            d.rmdir()
        return str(folder.relative_to(ROOT))
    async def _notify(self,reason,event):
        # ntfy.sh topics are bearer-by-URL unless separately protected, so omit coordinates and any credentials.
        now=time.monotonic();key=reason
        if now-self.last_notify.get(key,0)<300:return
        self.last_notify[key]=now
        text=f'CWA→Apple Weather 已回退 Apple 原始資料\n原因: {reason}\n模式: {MODE}\n耗時: {event.get("elapsedMs","?")} ms\n版本: {VERSION}'
        try:
            r=await self.ntfy.post(NTFY_URL,content=text.encode(),headers={'Title':'CWA Apple Proxy fallback','Priority':'high','Tags':'warning'});r.raise_for_status();self.stats['notifications']+=1
        except Exception:
            self.stats['notificationErrors']+=1
        else:
            try:
                payload={'time':int(time.time()),'mode':MODE,'topic':'cwa-apple-proxy','http':r.status_code,'receiptId':r.json().get('id'),'reason':reason,'elapsedMs':event.get('elapsedMs')}
                temp=ROOT/'data'/('notification-'+uuid.uuid4().hex+'.tmp');temp.write_text(json.dumps(payload));temp.replace(ROOT/'data/notification-last.json')
            except (OSError,ValueError,AttributeError):pass
    def notify_failure(self,reason,event):
        task=asyncio.create_task(self._notify(reason,event));self.notify_tasks.add(task);task.add_done_callback(self.notify_tasks.discard)
    async def response(self,flow):
        if flow.request.host!='weatherkit.apple.com':return
        self.transport_response(flow)
        self.stats['seen']+=1;location=self.target(flow)
        if not location or flow.response.status_code!=200 or not re.search(r'application/vnd\.apple\.flatbuffer\s*;\s*messageType=\"?WK2\.Weather(?:[\";\s]|$)',flow.response.headers.get('content-type',''),re.I):self.stats['passthrough']+=1;return
        original=flow.response.content;original_raw=flow.response.raw_content;headers=flow.response.headers.copy();started=time.monotonic();event={'mode':MODE,'version':VERSION,'time':int(time.time()),'latitude':location[0],'longitude':location[1],'status':'passthrough','app':flow.request.headers.get('user-agent','')}
        request_end=flow.request.timestamp_end;response_end=flow.response.timestamp_end
        if request_end is not None and response_end is not None and response_end>=request_end:event['appleResponseMs']=round((response_end-request_end)*1000)
        try:
            async with asyncio.timeout(DEADLINE):
                r=await self.client.get('http://100.78.140.101:18880/v1/cwa/weather',params={'latitude':location[0],'longitude':location[1],'country':'TW'});r.raise_for_status();snapshot=r.json()
                event['cwaMs']=round((time.monotonic()-started)*1000);codec_started=time.monotonic()
                r=await self.client.post('http://127.0.0.1:18881/transform',json={'body':base64.b64encode(original).decode(),'snapshot':snapshot});r.raise_for_status();mapped=r.json();body=base64.b64decode(mapped['body'],validate=True)
                event['codecMs']=round((time.monotonic()-codec_started)*1000)
            if time.monotonic()-started>DEADLINE:raise TimeoutError('translation deadline')
            report=mapped['report']
            if len(body)!=len(original) and not report.get('rebuiltRoots'):raise ValueError('Codec changed buffer length without verified root rebuild')
            if not 12<=len(body)<=4_000_000:raise ValueError('Codec output size invalid')
            if not report['modifiedFields'] and not report.get('rebuiltRoots'):self.stats['unchanged']+=1;event['status']='unchanged'
            else:
                event.update(status='modified',fields=report['modifiedFields'],skipped=report['skippedFields'],coverage=report.get('coverage',{}),station=snapshot['location']['stationId'],stationName=snapshot['location'].get('stationName'),temperature=snapshot['current']['temperature'],observationTime=snapshot['current']['observationTime']);proof_started=time.monotonic();event['proof']=self.proof(original,body,snapshot,report,event);event['proofMs']=round((time.monotonic()-proof_started)*1000)
                flow.response.content=body
                for name in ['etag','content-md5','digest','content-digest','age']:flow.response.headers.pop(name,None)
                flow.response.headers['cache-control']='private, max-age=120';flow.response.headers['x-cwa-bridge']=VERSION+'; cwa-first';flow.response.headers['x-cwa-station']=str(snapshot['location']['stationId']);self.stats['modified']+=1
        except Exception as e:
            flow.response.raw_content=original_raw;flow.response.headers=headers;self.stats['errors']+=1
            reason='timeout-3.5s' if isinstance(e,TimeoutError) else type(e).__name__;event.update(status='passthrough',error=type(e).__name__,fallbackReason=reason);event['elapsedMs']=round((time.monotonic()-started)*1000);self.notify_failure(reason,event)
        event.setdefault('elapsedMs',round((time.monotonic()-started)*1000))
        if flow.request.timestamp_start is not None:event['proxyTotalMs']=max(0,round((time.time()-flow.request.timestamp_start)*1000))
        self.record(event)
addons=[Bridge()]
