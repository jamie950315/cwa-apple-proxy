"""Exercise the deployed fallback handler with one isolated 3.5s delay.
The test sends one clearly-labelled notification to the user-requested topic.
Production CWA endpoints, routing and service state are untouched.
"""
import asyncio,json,time,tempfile
from pathlib import Path
from types import SimpleNamespace
import httpx
from mitmproxy import http
import addon
R=Path('/home/jamie/cwa-weather-proxy')
class DelayedCWA:
    async def get(self,*args,**kwargs):await asyncio.sleep(30)
async def main():
    receipt={}
    with tempfile.TemporaryDirectory(prefix='cwa-notify-selftest-') as folder:
        addon.ROOT=Path(folder);(addon.ROOT/'logs').mkdir();(addon.ROOT/'data').mkdir();addon.MODE='isolated-timeout-selftest'
        b=addon.Bridge();b.running();await b.client.aclose();b.client=DelayedCWA()
        actual=b.ntfy
        class RecordReceipt:
            async def post(self,url,**kwargs):
                kwargs['headers']['Title']='TEST: CWA 3.5s fallback notification'
                r=await actual.post(url,**kwargs)
                receipt.update(http=r.status_code,response=r.json())
                return r
        b.ntfy=RecordReceipt()
        f=SimpleNamespace(request=http.Request.make('GET','https://weatherkit.apple.com/api/v2/weather/zh-Hant-TW/25.09/121.56?country=TW'),response=http.Response.make(200,b'ISOLATED ORIGINAL APPLE RESPONSE',{'Content-Type':'application/vnd.apple.flatbuffer;messageType=WK2.Weather','ETag':'selftest-original'}))
        body=f.response.content;headers=f.response.headers.copy();start=time.monotonic();await b.response(f);elapsed=time.monotonic()-start
        assert 3.45<=elapsed<=4.5,elapsed
        assert f.response.content==body and f.response.headers==headers
        await asyncio.gather(*list(b.notify_tasks))
        assert receipt.get('http')==200 and receipt.get('response',{}).get('id'),receipt
        await actual.aclose()
        result={'time':int(time.time()),'isolatedTest':True,'handlerVersion':addon.VERSION,'deadlineSeconds':addon.DEADLINE,'fallbackElapsedSeconds':round(elapsed,4),'originalBodyPreserved':True,'originalHeadersPreserved':True,'notificationAfterFallback':True,'receipt':receipt,'stats':b.stats}
        (R/'reports/ntfy-timeout-selftest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print(json.dumps(result,ensure_ascii=False))
asyncio.run(main())
