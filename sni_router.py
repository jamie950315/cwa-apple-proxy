"""TLS passthrough router. Only weatherkit is terminated by the local bridge."""
import asyncio, json, os, time
BIND=os.getenv('BRIDGE_BIND','100.78.140.101')
PORT=int(os.getenv('SNI_PORT','19443'))
MAX_HELLO=65536

def parse_sni(hello: bytes):
    if len(hello)<4 or hello[0]!=1: return None
    n=int.from_bytes(hello[1:4],'big')
    if len(hello)<n+4: raise EOFError
    p=4+2+32
    p+=1+hello[p]
    p+=2+int.from_bytes(hello[p:p+2],'big')
    p+=1+hello[p]
    if p+2>n+4:return None
    end=p+2+int.from_bytes(hello[p:p+2],'big');p+=2
    while p+4<=end:
        kind=int.from_bytes(hello[p:p+2],'big');size=int.from_bytes(hello[p+2:p+4],'big');p+=4
        if p+size>end:raise ValueError('extension overflow')
        if kind==0:
            q=p+2
            while q+3<=p+size:
                t=hello[q];ln=int.from_bytes(hello[q+1:q+3],'big');q+=3
                if q+ln>p+size:raise ValueError('SNI overflow')
                if t==0:return hello[q:q+ln].decode('ascii').lower().rstrip('.')
                q+=ln
        p+=size
    return None

async def client_hello(reader):
    wire=bytearray(); handshake=bytearray()
    for _ in range(8):
        head=await reader.readexactly(5);n=int.from_bytes(head[3:5],'big')
        if head[0]!=22 or n>18432:raise ValueError('not a TLS ClientHello')
        body=await reader.readexactly(n);wire.extend(head+body);handshake.extend(body)
        if len(wire)>MAX_HELLO:raise ValueError('ClientHello too large')
        try:return bytes(wire),parse_sni(handshake)
        except EOFError:continue
    raise ValueError('fragment limit')

async def pipe(reader,writer):
    try:
        while chunk:=await asyncio.wait_for(reader.read(65536),120):
            writer.write(chunk);await writer.drain()
    except (ConnectionError,asyncio.TimeoutError):pass
    finally:
        try:writer.write_eof()
        except (OSError,RuntimeError,AttributeError):pass

async def handle(reader,writer):
    upstream=None
    try:
        wire,host=await asyncio.wait_for(client_hello(reader),10)
        target=('127.0.0.1',18443) if host=='weatherkit.apple.com' else (BIND,18444)
        ur,upstream=await asyncio.wait_for(asyncio.open_connection(*target),10)
        upstream.write(wire);await upstream.drain()
        await asyncio.gather(pipe(reader,upstream),pipe(ur,writer))
    except (OSError,ValueError,IndexError,UnicodeError,asyncio.TimeoutError,asyncio.IncompleteReadError):pass
    finally:
        writer.close()
        if upstream:upstream.close()

async def main():
    server=await asyncio.start_server(handle,[BIND,"127.0.0.1"],PORT,limit=MAX_HELLO)
    print(json.dumps({'service':'weather-sni-router','bind':BIND,'port':PORT}),flush=True)
    async with server:await server.serve_forever()
if __name__=='__main__':asyncio.run(main())
