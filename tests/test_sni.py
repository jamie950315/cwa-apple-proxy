import asyncio,ssl,pytest
from sni_router import client_hello,parse_sni
@pytest.mark.parametrize('host',['weatherkit.apple.com','pi5.tail19030f.ts.net','example.org'])
def test_clienthello(host):
 ctx=ssl.create_default_context();incoming,outgoing=ssl.MemoryBIO(),ssl.MemoryBIO()
 client=ctx.wrap_bio(incoming,outgoing,server_side=False,server_hostname=host)
 with pytest.raises(ssl.SSLWantReadError):client.do_handshake()
 wire=outgoing.read()
 async def parse(data):
  reader=asyncio.StreamReader();reader.feed_data(data);reader.feed_eof();return await client_hello(reader)
 saved,sni=asyncio.run(parse(wire));assert sni==host;assert saved==wire
 handshake=wire[5:]
 split=len(handshake)//2
 fragments=b'\x16\x03\x01'+split.to_bytes(2,'big')+handshake[:split]+b'\x16\x03\x01'+(len(handshake)-split).to_bytes(2,'big')+handshake[split:]
 saved,sni=asyncio.run(parse(fragments));assert sni==host;assert saved==fragments

@pytest.mark.parametrize('split',[1,2,3])
def test_clienthello_header_can_span_records(split):
 ctx=ssl.create_default_context();incoming,outgoing=ssl.MemoryBIO(),ssl.MemoryBIO()
 client=ctx.wrap_bio(incoming,outgoing,server_side=False,server_hostname='weatherkit.apple.com')
 with pytest.raises(ssl.SSLWantReadError):client.do_handshake()
 handshake=outgoing.read()[5:]
 fragments=b'\x16\x03\x01'+split.to_bytes(2,'big')+handshake[:split]+b'\x16\x03\x01'+(len(handshake)-split).to_bytes(2,'big')+handshake[split:]
 async def parse():
  reader=asyncio.StreamReader();reader.feed_data(fragments);reader.feed_eof();return await client_hello(reader)
 saved,sni=asyncio.run(parse());assert saved==fragments;assert sni=='weatherkit.apple.com'

def test_clienthello_rejects_extension_bytes_outside_declared_handshake():
 ctx=ssl.create_default_context();incoming,outgoing=ssl.MemoryBIO(),ssl.MemoryBIO()
 client=ctx.wrap_bio(incoming,outgoing,server_side=False,server_hostname='weatherkit.apple.com')
 with pytest.raises(ssl.SSLWantReadError):client.do_handshake()
 handshake=bytearray(outgoing.read()[5:])
 handshake[1:4]=(len(handshake)-5).to_bytes(3,'big')
 with pytest.raises(ValueError):parse_sni(handshake)
