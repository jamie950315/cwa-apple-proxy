/* Preserve opaque original payload while adding omitted scalar fields.
 * Clone only tables/vectors on paths to changed fields; all known pointers are
 * relocated. An unrecognized populated table slot makes expansion fail closed.
 */
import {Weather,ByteBuffer} from './vendor/weatherkit-codec.full.mjs';
const SIZE={Int8:1,Uint8:1,Int16:2,Uint16:2,Int32:4,Uint32:4,Float32:4,Float64:8};
const align=(n,a)=>Math.ceil(n/a)*a;
export function expandScalars(source,patches){
 if(!patches.length)return {bytes:source,insertions:[],prefixBytes:0};
 const dv=new DataView(source.buffer,source.byteOffset,source.byteLength),bb=new ByteBuffer(source);
 const graph=new Map(),wanted=new Map();
 for(const p of patches){if(!wanted.has(p.tablePos))wanted.set(p.tablePos,[]);wanted.get(p.tablePos).push(p);}
 function check(pos,size){if(!Number.isInteger(pos)||pos<4||pos+size>source.length)throw Error('Expansion bounds');}
 function table(t){
  const pos=t.bb_pos;if(graph.has(pos))return graph.get(pos);check(pos,4);
  const vt=pos-dv.getInt32(pos,true);check(vt,4);
  const vlen=dv.getUint16(vt,true),osize=dv.getUint16(vt+2,true);check(vt,vlen);check(pos,osize);
  if(vlen<4||vlen%2||osize<4)throw Error('Expansion invalid table');
  const node={kind:'table',pos,vt,vlen,osize,edges:[],references:[],schema:new Set(),patches:wanted.get(pos)||[]};graph.set(pos,node);
  if(graph.size>20000)throw Error('Expansion node limit');
  for(const name of Object.getOwnPropertyNames(Object.getPrototypeOf(t))){
   if(name==="constructor")continue;
   if(typeof t[name]!=='function')continue;
   const body=t[name].toString(),m=body.match(/__offset\(this\.bb_pos,\s*(\d+)\)/);if(!m)continue;
   const index=Number(m[1]);node.schema.add(index);
   const off=index<vlen?dv.getUint16(vt+index,true):0;if(!off)continue;
   if(!body.includes('__indirect')&&!body.includes('__vector')&&!body.includes('__string'))continue;
   if(name.endsWith('Length')||name.endsWith('Array'))continue;
   check(pos+off,4);const target=pos+off+dv.getUint32(pos+off,true);check(target,4);
   node.references.push({off,target});
   if(pos===dv.getUint32(0,true)&&!['currentWeather','forecastHourly','forecastDaily'].includes(name))continue;
   if(body.includes('__indirect')){
    if(body.includes('__vector')){
     let vector=graph.get(target);
     if(!vector){
      const count=dv.getUint32(target,true);if(count>10000)throw Error('Expansion vector length');check(target,4+4*count);
      vector={kind:'vector',pos:target,count,edges:[],references:[]};graph.set(target,vector);
      for(let i=0;i<count;i++){const pp=target+4+4*i,tp=pp+dv.getUint32(pp,true);try{check(tp,4);}catch(e){throw Error(`Expansion vector ${name}[${i}]/${count} at ${target} target ${tp}`)}const child=table(t[name](i));if(child.pos!==tp)throw Error('Expansion vector target mismatch');vector.edges.push(child);vector.references.push({off:4+4*i,target:tp});}
     }
     node.edges.push(vector);
    }else node.edges.push(table(t[name]()));
   }
  }
  // WK2.Weather is a root collection of table offsets. Preserve newer roots
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
 const root=table(Weather.getRootAsWeather(bb));
 for(const pos of wanted.keys())if(!graph.has(pos))throw Error('Expansion patch target unreachable');
 const state=new Map();
 function needed(n){if(state.get(n)===1)throw Error('Expansion graph cycle');if(state.get(n)===2)return n.needed;state.set(n,1);const child=n.edges.map(needed).some(Boolean);n.needed=Boolean(n.patches?.length||child);state.set(n,2);return n.needed;}
 needed(root);
 const order=[],seen=new Set();
 function post(n){if(seen.has(n)||!n.needed)return;seen.add(n);for(const e of n.edges)post(e);order.push(n);}
 post(root);order.reverse();
 let cursor=8;
 for(const n of order){
  if(n.kind==='vector'){cursor=align(cursor,4);n.out=cursor;cursor+=4+4*n.count;continue;}
  // Refuse to relocate a populated field whose scalar/pointer type is unknown.
  for(let i=4;i<n.vlen;i+=2)if(dv.getUint16(n.vt+i,true)&&!n.schema.has(i))throw Error('Expansion unknown populated slot '+i);
  n.newVlen=Math.max(n.vlen,...n.patches.map(p=>p.index+2));n.newSize=n.osize;
  for(const p of n.patches){if(!SIZE[p.type]||!Number.isFinite(p.value)||!n.schema.has(p.index))throw Error('Expansion invalid scalar');n.newSize=align(n.pos+n.newSize,SIZE[p.type])-n.pos;p.newOffset=n.newSize;n.newSize+=SIZE[p.type];}
  if(n.newSize>65535||n.newVlen>65535)throw Error('Expansion table too large');
  cursor=align(cursor,2);n.outVT=cursor;cursor+=n.newVlen;cursor=align(cursor,8)+(n.pos%8);n.out=cursor;cursor+=align(n.newSize,8);
 }
 const prefixBytes=align(cursor,8),out=new Uint8Array(prefixBytes+source.length),view=new DataView(out.buffer);
 out.set(source,prefixBytes);out.set(source.subarray(4,8),4);view.setUint32(0,root.out,true);
 const insertions=[];
 for(const n of order){
  if(n.kind==='vector'){out.set(source.subarray(n.pos,n.pos+4+4*n.count),n.out);}
  else{
   out.set(source.subarray(n.vt,n.vt+n.vlen),n.outVT);view.setUint16(n.outVT,n.newVlen,true);view.setUint16(n.outVT+2,n.newSize,true);
   out.set(source.subarray(n.pos,n.pos+n.osize),n.out);view.setInt32(n.out,n.out-n.outVT,true);
   for(const p of n.patches){view.setUint16(n.outVT+p.index,p.newOffset,true);view['set'+p.type](n.out+p.newOffset,p.value,true);insertions.push({field:p.field,before:p.before,after:view['get'+p.type](n.out+p.newOffset,true),offset:n.out+p.newOffset,size:SIZE[p.type],source:p.source,inserted:true});}
  }
  for(const ref of n.references){const child=graph.get(ref.target);const target=child?.needed?child.out:prefixBytes+ref.target;const pp=n.out+ref.off;if(target<=pp)throw Error('Expansion non-forward pointer');view.setUint32(pp,target-pp,true);}
 }
 if(out.length>4_000_000)throw Error('Expanded response too large');
 return {bytes:out,insertions,prefixBytes,clonedTables:order.filter(n=>n.kind==='table').length};
}
