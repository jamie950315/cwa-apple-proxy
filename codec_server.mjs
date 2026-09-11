import http from 'node:http';
import {transform,VERSION} from './mapper.mjs';
const stats={requests:0,modified:0,errors:0};
const server=http.createServer(async(req,res)=>{
 res.setHeader('content-type','application/json');
 if(req.method==='GET'&&req.url==='/healthz'){res.end(JSON.stringify({service:'weather-flatbuffers-codec',version:VERSION,...stats}));return;}
 if(req.method!=='POST'||req.url!=='/transform'){res.statusCode=404;res.end('{}');return;}
 const chunks=[];let size=0;
 try{
  for await(const chunk of req){size+=chunk.length;if(size>8000000)throw Error('Body too large');chunks.push(chunk);}
  const input=JSON.parse(Buffer.concat(chunks).toString('utf8'));stats.requests++;
  if(typeof input.body!=='string')throw Error('Missing body');
  const {bytes,report}=transform(new Uint8Array(Buffer.from(input.body,'base64')),input.snapshot);
  stats.modified+=report.modifiedFields;
  res.end(JSON.stringify({body:Buffer.from(bytes).toString('base64'),report}));
 }catch(e){stats.errors++;res.statusCode=422;res.end(JSON.stringify({error:e.message}));}
});
server.requestTimeout=20000;server.headersTimeout=10000;server.maxHeadersCount=50;
server.listen(18881,'127.0.0.1',()=>console.log(`Weather codec ${VERSION} listening on loopback:18881`));
