import fs from 'node:fs';
import {Weather,ByteBuffer,WeatherKit2} from '../vendor/weatherkit-codec.full.mjs';
const src=JSON.parse(fs.readFileSync(new URL('./actual-brief.json',import.meta.url))).source;
const bytes=new Uint8Array(fs.readFileSync(new URL(`./apple-${src.id}.bin`,import.meta.url))),bb=new ByteBuffer(bytes),view=new DataView(bytes.buffer);
const root=Weather.getRootAsWeather(bb),periodClass=root.forecastDaily().days(0).daytimeForecast().constructor;
function table(p){const vt=p-view.getInt32(p,true),len=view.getUint16(vt,true),size=view.getUint16(vt+2,true);let fields=[];for(let i=4;i<len;i+=2){const off=view.getUint16(vt+i,true);if(off)fields.push({slot:i,off,u32:off+4<=size?view.getUint32(p+off,true):null,f32:off+4<=size?view.getFloat32(p+off,true):null});}return {position:p,vt,len,size,fields};}
const rootLayout=table(root.bb_pos),off=rootLayout.fields.find(x=>x.slot===28).off,collectionPos=root.bb_pos+off+view.getUint32(root.bb_pos+off,true),layout=table(collectionPos);
const vectorField=layout.fields.find(x=>x.slot===6),vptr=collectionPos+vectorField.off,vector=vptr+view.getUint32(vptr,true),count=view.getUint32(vector,true),items=[];
for(let i=0;i<Math.min(count,6);i++){
 const ptr=vector+4+4*i,pos=ptr+view.getUint32(ptr,true),p=new periodClass().__init(pos,bb),values={};
 for(const key of Object.getOwnPropertyNames(periodClass.prototype)){if(key==='constructor'||typeof p[key]!=='function')continue;const code=p[key].toString();if(!/\.read(?:U?int|Int|Float)/.test(code))continue;try{values[key]=p[key]();}catch(e){values[key]='error';}}
 items.push({layout:table(pos),asDayPart:values});
}
fs.writeFileSync(new URL('./periodic-inspection.json',import.meta.url),JSON.stringify({src,collection:layout,count,items},null,2));
