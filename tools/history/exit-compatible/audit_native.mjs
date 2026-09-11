import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {Weather,WeatherKit2,ByteBuffer} from '../../vendor/weatherkit-codec.full.mjs';
const base='/home/jamie/cwa-weather-proxy',dir=path.join(base,'research/exit-compatible');
const list=JSON.parse(fs.readFileSync(path.join(dir,'native-proof-list.json')));
const index=JSON.parse(fs.readFileSync(path.join(dir,'native-proof-index.json')));
const items=[];
for(const folder of list){
 try{
  const req=JSON.parse(fs.readFileSync(path.join(folder,'request.json'))),report=JSON.parse(fs.readFileSync(path.join(folder,'report.json'))),snap=JSON.parse(fs.readFileSync(path.join(folder,'cwa.json')));
  const output=new Uint8Array(fs.readFileSync(path.join(folder,'mapped.bin'))),original=new Uint8Array(fs.readFileSync(path.join(folder,'original.bin')));
  const root=Weather.getRootAsWeather(new ByteBuffer(output));let checked=0;
  for(const c of report.changes){
   const m=c.field.match(/^(current|hour\[(\d+)\]|day\[(\d+)\])(?:\.(daytimeForecast|overnightForecast|restOfDayForecast))?\.(\w+)$/);
   assert.ok(m,'unknown change path '+c.field);
   let t=m[1]==='current'?root.currentWeather():m[2]!==undefined?root.forecastHourly().hours(Number(m[2])):root.forecastDaily().days(Number(m[3]));
   if(m[4])t=t[m[4]]();assert.ok(t&&typeof t[m[5]]==='function');
   const actual=t[m[5]]();assert.ok(Math.abs(actual-c.after)<=Math.max(0.0001,Math.abs(c.after)*1e-6),c.field+' mismatch');checked++;
  }
  assert.ok(Math.abs(root.currentWeather().temperature()-snap.current.temperature)<0.0001);
  if(snap.airQuality){const a=WeatherKit2.decode(new ByteBuffer(output),['airQuality']).airQuality;assert.equal(a.index,snap.airQuality.index);assert.equal(a.scale,snap.airQuality.scale);}
  items.push({status:'passed',exit:index[folder].exit,time:req.time,app:req.app,folder:path.relative(base,folder),checkedFields:checked,skipped:report.skippedFields,temperature:root.currentWeather().temperature(),sourceTemperature:snap.current.temperature,station:req.stationName,coverage:report.coverage,inputBytes:original.length,outputBytes:output.length});
 }catch(e){items.push({status:'failed',folder,error:String(e)})}
}
const report={count:items.length,passed:items.filter(x=>x.status==='passed').length,checkedFields:items.reduce((a,b)=>a+(b.checkedFields||0),0),items};
fs.writeFileSync(path.join(dir,'native-audit.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({count:report.count,passed:report.passed,checkedFields:report.checkedFields}));
if(!items.length||items.some(x=>x.status==='failed'))process.exitCode=1;
