// Audit real iOS responses without modifying the running translation service.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {Weather, WeatherKit2, ByteBuffer} from '../../vendor/weatherkit-codec.full.mjs';
const base='/home/jamie/cwa-weather-proxy';
const destination=path.join(base,'reports/iphone-native');
fs.mkdirSync(destination,{recursive:true,mode:0o700});
const rows=fs.readFileSync(path.join(base,'logs/bridge-reverse.jsonl'),'utf8').split('\n').flatMap(line=>{try{return [JSON.parse(line)];}catch{return [];}}).filter(r=>/iOS|iPhoneOS|iPadOS/.test(r.app||''));
const items=[];
for(const req of rows){
 if(req.status!=='modified'){items.push({status:'failed',time:req.time,app:req.app,error:req.error||req.status});continue;}
 try{
  assert.ok(/^data\/proofs\/[a-f0-9-]+$/.test(req.proof),'Unexpected evidence path');
  const folder=path.join(destination,path.basename(req.proof));
  if(!fs.existsSync(folder))fs.cpSync(path.join(base,req.proof),folder,{recursive:true,errorOnExist:true,force:false});
  const report=JSON.parse(fs.readFileSync(path.join(folder,'report.json')));
  const snap=JSON.parse(fs.readFileSync(path.join(folder,'cwa.json')));
  const mapped=new Uint8Array(fs.readFileSync(path.join(folder,'mapped.bin')));
  const original=new Uint8Array(fs.readFileSync(path.join(folder,'original.bin')));
  const root=Weather.getRootAsWeather(new ByteBuffer(mapped));
  const before=Weather.getRootAsWeather(new ByteBuffer(original));
  let checked=0;
  for(const c of report.changes){
   const m=c.field.match(/^(current|hour\[(\d+)\]|day\[(\d+)\])(?:\.(daytimeForecast|overnightForecast|restOfDayForecast))?\.(\w+)$/);
   assert.ok(m,'Unknown changed field '+c.field);
   let table=m[1]==='current'?root.currentWeather():m[2]!==undefined?root.forecastHourly().hours(Number(m[2])):root.forecastDaily().days(Number(m[3]));
   if(m[4])table=table[m[4]]();
   assert.ok(table&&typeof table[m[5]]==='function','Missing getter '+c.field);
   const actual=table[m[5]]();
   assert.ok(Number.isFinite(actual)&&Math.abs(actual-c.after)<=Math.max(0.0001,Math.abs(c.after)*1e-6),'Mismatch '+c.field);
   checked++;
  }
  assert.equal(checked,report.modifiedFields);
  assert.ok(Math.abs(root.currentWeather().temperature()-snap.current.temperature)<0.0001,'CWA temperature mismatch');
  assert.equal(root.currentWeather().asOf(),snap.current.observationTime);
  const decoded=WeatherKit2.decode(new ByteBuffer(mapped),['airQuality','weatherAlerts']);
  if(snap.airQuality){assert.equal(decoded.airQuality.index,snap.airQuality.index);assert.equal(decoded.airQuality.scale,snap.airQuality.scale);}
  if(snap.weatherAlerts)for(const alert of snap.weatherAlerts.alerts)assert.ok(decoded.weatherAlerts.alerts.some(a=>a.id===alert.id),'Missing CWA alert');
  const stats={};
  for(const key of ['temperature','temperatureApparent','humidity','windSpeed','pressure','precipitationAmount1h','precipitationAmount6h','precipitationAmount24h','precipitationAmountNext1h','precipitationAmountNext6h','precipitationAmountNext24h']){
   if(typeof root.currentWeather()[key]==='function')stats[key]={apple:before.currentWeather()[key](),sent:root.currentWeather()[key]()};
  }
  items.push({status:'passed',time:req.time,localTime:new Date(req.time*1000).toLocaleString('sv-SE',{timeZone:'Asia/Taipei'}),app:req.app,station:req.stationName,stationId:req.station,checkedFields:checked,skipped:report.skippedFields,coverage:report.coverage,elapsedMs:req.elapsedMs,sourceTemperature:snap.current.temperature,observationTime:snap.current.observationTime,current:stats,aqi:decoded.airQuality?{index:decoded.airQuality.index,scale:decoded.airQuality.scale}:null,inputBytes:original.length,outputBytes:mapped.length,evidence:path.relative(base,folder)});
 }catch(e){items.push({status:'failed',time:req.time,app:req.app,error:String(e),proof:req.proof});}
}
const result={verifiedAt:new Date().toISOString(),count:items.length,passed:items.filter(i=>i.status==='passed').length,failures:items.filter(i=>i.status!=='passed'),appResponses:items.filter(i=>i.status==='passed'&&i.app.includes('Weather_iOS')).length,widgetResponses:items.filter(i=>i.status==='passed'&&i.app.includes('WeatherWidget_iOS')).length,items};
fs.writeFileSync(path.join(base,'reports/iphone-native-audit.json'),JSON.stringify(result,null,2),{mode:0o600});
console.log(JSON.stringify(result,null,2));
if(result.count===0||result.failures.length)process.exitCode=1;
