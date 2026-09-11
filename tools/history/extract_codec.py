from pathlib import Path
import re,hashlib,json
base=Path('/home/jamie/cwa-weather-proxy')
s=(base/'research/response.bundle.js').read_text()
# Public Apache-2.0 distribution; remove the proxy-product runner entirely.
start=s.index('const t=')
end=s.rfind('(async()=>{$response=await Pt(')
assert end>start
s=s[start:end]
assert s.endswith('}') or s.endswith(';')
s+='\ne.logLevel="OFF";\nexport {Nt as WeatherKit2,p as ByteBuffer,ht as Weather,e as Console};\n'
p=base/'vendor';p.mkdir(exist_ok=True)
(p/'weatherkit-codec.full.mjs').write_text(s)
(p/'LICENSE-WeatherKit').write_bytes((base/'research/WeatherKit/LICENSE').read_bytes())
(p/'NOTICE').write_text('WeatherKit codec derived from NSRingo/WeatherKit v3.3.2 response.bundle.js.\nCopyright its respective contributors. Licensed under Apache-2.0.\nModifications: remove application runner and external-provider usage; export local FlatBuffers codec.\nSource: https://github.com/NSRingo/WeatherKit/releases/tag/v3.3.2\nBundle SHA256: '+hashlib.sha256((base/'research/response.bundle.js').read_bytes()).hexdigest()+'\n')
print('Extracted',len(s),'bytes')
