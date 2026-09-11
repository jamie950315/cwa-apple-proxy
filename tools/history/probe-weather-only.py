from mitmproxy import http
from pathlib import Path
import json,time,urllib.parse
ROOT=Path('/home/jamie/cwa-weather-proxy')
def http_connect(flow):
    if flow.request.host != 'weatherkit.apple.com':
        flow.response=http.Response.make(403,b'Weather-only proxy')
def request(flow):
    if flow.request.host == 'weatherkit.apple.com':
        flow.request.headers.pop('If-None-Match',None)
        flow.request.headers.pop('If-Modified-Since',None)
def response(flow):
    if flow.request.host != 'weatherkit.apple.com':return
    parts=urllib.parse.urlsplit(flow.request.pretty_url)
    safe={k:v for k,v in urllib.parse.parse_qs(parts.query).items() if k in ('dataSets','country','timezone','timeZone','hourlyStart','hourlyEnd','dailyStart','dailyEnd')}
    stamp=str(time.time_ns())
    body=flow.response.content
    rec={'id':stamp,'host':flow.request.host,'path':parts.path,'query':safe,'method':flow.request.method,'status':flow.response.status_code,'contentType':flow.response.headers.get('content-type'),'bytes':len(body),'userAgent':flow.request.headers.get('user-agent'),'accept':flow.request.headers.get('accept'),'time':time.time()}
    (ROOT/'research'/f'apple-{stamp}.bin').write_bytes(body)
    (ROOT/'research'/f'apple-{stamp}.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2))
    with (ROOT/'logs'/'capture.jsonl').open('a') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
