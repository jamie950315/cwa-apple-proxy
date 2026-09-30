import asyncio
from pathlib import Path

import httpx
import pytest
import model_worker


def worker_setup(tmp_path,monkeypatch,handler):
    (tmp_path/'data').mkdir()
    monkeypatch.setattr(model_worker,'ROOT',tmp_path)
    monkeypatch.setattr(model_worker,'HOURS',[6])
    monkeypatch.setattr(model_worker,'FIELDS',{'apcp':(0,12,0,1,8),'pressure':(36,12,0,3,1)})
    monkeypatch.setattr(model_worker,'TOWNS',[{'county':'test','town':'test'}])
    monkeypatch.setattr(model_worker,'decode',lambda blob,kind,hour,geometry:{'initialTime':1,'leadHours':hour,'values':[1]})
    client_class=httpx.AsyncClient
    monkeypatch.setattr(model_worker.httpx,'AsyncClient',lambda **kwargs:client_class(transport=httpx.MockTransport(handler)))


def test_cached_subsets_are_validated_without_rewriting_or_hashing(tmp_path,monkeypatch):
    requests=[]
    def handler(request):
        requests.append(request.method)
        if request.method=='HEAD':return httpx.Response(200,headers={'etag':'same','content-length':'60'})
        start_end=request.headers['Range'].split('=')[1]
        return httpx.Response(206,headers={'content-range':f'bytes {start_end}/60'},content=b'x'*12)
    worker_setup(tmp_path,monkeypatch,handler)
    asyncio.run(model_worker.main())
    writes=[];write_bytes=Path.write_bytes;write_text=Path.write_text
    def record_bytes(path,data):writes.append(path);return write_bytes(path,data)
    def record_text(path,data,*args,**kwargs):writes.append(path);return write_text(path,data,*args,**kwargs)
    monkeypatch.setattr(Path,'write_bytes',record_bytes)
    monkeypatch.setattr(Path,'write_text',record_text)
    def unexpected_hash(_):raise AssertionError('Unchanged subsets must not be rehashed')
    monkeypatch.setattr(model_worker.hashlib,'sha256',unexpected_hash)
    asyncio.run(model_worker.main())
    assert requests==['HEAD','GET','GET','HEAD']
    assert not any(path.parent.name=='model-subsets' for path in writes)


def test_failed_apcp_does_not_discard_independent_pressure(tmp_path,monkeypatch):
    def handler(request):
        if request.method=='HEAD':return httpx.Response(200,headers={'etag':'same','content-length':'60'})
        if request.headers['Range']=='bytes=0-11':return httpx.Response(503)
        return httpx.Response(206,headers={'content-range':'bytes 36-47/60'},content=b'x'*12)
    worker_setup(tmp_path,monkeypatch,handler)
    asyncio.run(model_worker.main())
    import json
    product=json.loads((tmp_path/'data/model-wrf.json').read_text())
    assert 'pressure' in product['fields'] and 'apcp' not in product['fields']


def test_oversized_range_stops_reading_at_the_bound(tmp_path,monkeypatch):
    chunks=[]
    class Oversized(httpx.AsyncByteStream):
        async def __aiter__(self):
            for i in range(3):chunks.append(i);yield b'x'*13
    def handler(request):
        if request.method=='HEAD':return httpx.Response(200,headers={'etag':'same','content-length':'60'})
        start_end=request.headers['Range'].split('=')[1]
        return httpx.Response(206,headers={'content-range':f'bytes {start_end}/60'},stream=Oversized())
    worker_setup(tmp_path,monkeypatch,handler)
    with pytest.raises(RuntimeError,match='No validated model subsets'):asyncio.run(model_worker.main())
    assert chunks and all(i==0 for i in chunks)
