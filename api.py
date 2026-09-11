"""Tailnet-only diagnostics, CWA normalized data, and certificate onboarding."""
from contextlib import asynccontextmanager,suppress
import asyncio,json,time,hashlib
from pathlib import Path
from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import FileResponse,Response
import httpx
from cwa_client import Store,Unavailable,ROOT
from cwa_snapshot import snapshot
VERSION='0.3.1'
store=None
request_limit=asyncio.Semaphore(12)
async def warmup():
    while True:
        await asyncio.gather(store.get('O-A0003-001'),store.get('O-A0001-001'),store.get('O-A0002-001'),store.file_get('F-B0046-001'),store.file_get('O-A0038-003'),store.get('W-C0033-001'),store.get('W-C0033-002'),store.get('A-B0062-001'),store.get('A-B0063-001'),store.linked_aqi(),return_exceptions=True)
        await asyncio.sleep(300)
@asynccontextmanager
async def lifespan(app):
    global store
    store=Store();task=asyncio.create_task(warmup())
    try:yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):await task
        await store.close()
app=FastAPI(title='CWA Weather Bridge',version=VERSION,lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)

def read_json(path,default=None):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return default

@app.get('/healthz')
async def health():return {'service':'cwa-weather-bridge','version':VERSION,'time':int(time.time()),'cwa':store.health()}

@app.get('/status')
async def status():
    result=await health();result['bridge']=read_json(ROOT/'data/bridge-status.json',{})
    result['forwardBridge']=read_json(ROOT/'data/bridge-status-forward.json',{})
    result['routing']=read_json(ROOT/'data/routing-status.json',{})
    result['splitRoutes']=read_json(ROOT/'data/split-route-status.json',{})
    result['exitCompatibility']=read_json(ROOT/'data/exit-compatibility-status.json',{})
    result['notification']=read_json(ROOT/'data/notification-last.json',{})
    result['notificationTest']=read_json(ROOT/'reports/ntfy-timeout-selftest.json',{})
    result['clients']=read_json(ROOT/'clients.json',{})
    result['certificateSha256']=hashlib.sha256((ROOT/'certs/ca.cer').read_bytes()).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=1,trust_env=False) as c:
            r=await c.get('http://127.0.0.1:18881/healthz');r.raise_for_status();result['codec']=r.json()
    except httpx.HTTPError:result['codec']={'status':'unavailable'}
    event=result['bridge'].get('last',{});proof=event.get('proof')
    if proof:
        p=(ROOT/proof).resolve()
        if p.is_relative_to((ROOT/'data/proofs').resolve()):
            report=read_json(p/'report.json',{})
            result['lastProof']={'report':report,'cwa':read_json(p/'cwa.json',{}),'request':read_json(p/'request.json',{})}
    result['mode']='CWA-first observations, analyzed temperature, rain gauges, radar QPF and township forecast; 3.5s Apple fallback with ntfy alerts'
    return result

@app.get('/v1/cwa/weather')
async def weather(latitude:float=Query(ge=-90,le=90),longitude:float=Query(ge=-180,le=180),country:str='TW'):
    try:
        async with request_limit:return await snapshot(store,latitude,longitude,country)
    except (Unavailable,ValueError) as e:raise HTTPException(503,detail=str(e)) from None

@app.get('/ca.cer')
async def ca_der():return FileResponse(ROOT/'certs/ca.cer',media_type='application/pkix-cert')
@app.get('/ca.pem')
async def ca_pem():return FileResponse(ROOT/'certs/ca.pem',media_type='application/x-pem-file')
@app.get('/CWA-Weather.mobileconfig')
async def profile():return FileResponse(ROOT/'data/CWA-Weather.mobileconfig',media_type='application/x-apple-aspen-config')
@app.get('/proxy.pac')
async def pac():
    return Response('function FindProxyForURL(url,host){if(host === "weatherkit.apple.com")return "PROXY 100.78.140.101:18940";return "DIRECT";}',media_type='application/x-ns-proxy-autoconfig')
@app.get('/source.zip')
async def source():
    p=ROOT/'dist/cwa-weather-bridge-source.zip'
    if not p.exists():raise HTTPException(404)
    return FileResponse(p,media_type='application/zip',filename=p.name)
@app.get('/')
async def index():return FileResponse(ROOT/'dashboard.html',media_type='text/html')

@app.get('/audit')
async def audit():return read_json(ROOT/'reports/source-audit.json',{'status':'report being updated'})
