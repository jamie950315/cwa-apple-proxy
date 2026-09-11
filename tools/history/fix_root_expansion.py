from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/flatbuffer_expand.mjs');s=p.read_text();token='  return node;\n }\n const root='
s=s.replace(token,'''  // WK2.Weather is a root collection of table offsets. Preserve newer roots
  // absent from the vendored getter set after validating their target tables.
  if(pos===dv.getUint32(0,true))for(let i=4;i<vlen;i+=2){
   const off=dv.getUint16(vt+i,true);if(!off||node.schema.has(i))continue;
   check(pos+off,4);const target=pos+off+dv.getUint32(pos+off,true);check(target,4);
   const tv=target-dv.getInt32(target,true);check(tv,4);const tl=dv.getUint16(tv,true),sz=dv.getUint16(tv+2,true);
   if(tl<4||tl%2||sz<4)throw Error('Expansion unknown root is not a table');check(tv,tl);check(target,sz);
   node.schema.add(i);node.references.push({off,target});
  }
  return node;
 }
 const root=''' )
p.write_text(s)
p=Path('/home/jamie/cwa-weather-proxy/research/root_layout.mjs');p.write_text(p.read_text().replace('new DataView(bytes.buffer)','new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength)'))
