import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {Weather,WeatherKit2,ByteBuffer} from '../vendor/weatherkit-codec.full.mjs';
const ROOT='/home/jamie/cwa-weather-proxy';
const reports=[];
for(const name of fs.readdirSync(path.join(ROOT,'data/proofs'))){
 const dir=path.join(ROOT,'data/proofs',name);
 try{
  const report=JSON.parse(fs.readFileSync(path.join(dir,'report.json')));
  const request=JSON.parse(fs.readFileSync(path.join(dir,'request.json')));
  if(report.version!=='0.3.1'||!String(request.app).includes('WeatherKit_'))continue;
  const snapshot=JSON.parse(fs.readFileSync(path.join(dir,'cwa.json')));
  const mapped=new Uint8Array(fs.readFileSync(path.join(dir,'mapped.bin')));
  const original=new Uint8Array(fs.readFileSync(path.join(dir,'original.bin')));
  const root=Weather.getRootAsWeather(new ByteBuffer(mapped));
  let checked=0;
  for(const change of report.changes){
   const label=change.field;let obj;
   if(label.startsWith('current.'))obj=root.currentWeather();
   else if(label.startsWith('hour['))obj=root.forecastHourly().hours(Number(label.match(/^hour\[(\d+)\]/)[1]));
   else if(label.startsWith('day[')){
    obj=root.forecastDaily().days(Number(label.match(/^day\[(\d+)\]/)[1]));
    const parts=label.split('.');if(parts.length===3)obj=obj[parts[1]]();
   }else continue;
   const key=label.split('.').at(-1);const actual=obj[key]();
   assert.ok(Math.abs(actual-change.after)<=Math.max(1e-5,Math.abs(change.after)*1e-6),`${label}: ${actual} vs ${change.after}`);checked++;
  }
  const aqi=WeatherKit2.decode(new ByteBuffer(mapped),['airQuality']).airQuality;
  if(snapshot.airQuality){assert.equal(aqi.index,snapshot.airQuality.index);assert.equal(aqi.scale,snapshot.airQuality.scale);}
  const alert=WeatherKit2.decode(new ByteBuffer(mapped),['weatherAlerts']).weatherAlerts;
  if(snapshot.weatherAlerts)for(const a of snapshot.weatherAlerts.alerts)assert.ok(alert.alerts.some(v=>v.id===a.id),'CWA alert missing');
  const current=root.currentWeather();
  const daily=root.forecastDaily();
  reports.push({status:'passed',proof:`data/proofs/${name}`,app:request.app,time:request.time,station:snapshot.location.stationName,temperature:current?.temperature(),asOf:current?.asOf(),checkedScalarChanges:checked,skipped:report.skippedFields,inputBytes:original.length,outputBytes:mapped.length,coverage:report.coverage,rebuiltRoots:report.rebuiltRoots,aqi:aqi?{index:aqi.index,scale:aqi.scale,provider:aqi.metadata?.providerName}:null,firstDay:daily?.daysLength()?{sunrise:daily.days(0).sunrise(),sunset:daily.days(0).sunset(),precipitationAmount:daily.days(0).precipitationAmount()}:null});
 }catch(error){reports.push({status:'failed',proof:name,error:error.message});}
}
reports.sort((a,b)=>(a.time||0)-(b.time||0));
const result={auditedAt:new Date().toISOString(),method:'Read retained actual macOS Weather and WeatherWidget response proofs; compare all reported changes with native FlatBuffer getters.',count:reports.length,passed:reports.filter(x=>x.status==='passed').length,failures:reports.filter(x=>x.status==='failed'),latest:reports.slice(-5),all:reports};
fs.writeFileSync(path.join(ROOT,'reports/native-031-audit.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({count:result.count,passed:result.passed,failures:result.failures,latest:result.latest.map(({rebuiltRoots,...p})=>p)},null,2));
if(result.failures.length||!result.count)process.exitCode=1;
