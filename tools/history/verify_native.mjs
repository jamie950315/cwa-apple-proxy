import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {WeatherKit2,ByteBuffer} from '../vendor/weatherkit-codec.full.mjs';
const ROOT='/home/jamie/cwa-weather-proxy',dir=path.join(ROOT,'data/proofs');
const selected=[];
for(const name of fs.readdirSync(dir)){
 const folder=path.join(dir,name),event=JSON.parse(fs.readFileSync(path.join(folder,'request.json')));
 if(event.version!=='0.2.0'||!event.app.includes('WeatherKit_Weather_macOS'))continue;
 const original=new Uint8Array(fs.readFileSync(path.join(folder,'original.bin'))),mapped=new Uint8Array(fs.readFileSync(path.join(folder,'mapped.bin')));
 const snapshot=JSON.parse(fs.readFileSync(path.join(folder,'cwa.json'))),report=JSON.parse(fs.readFileSync(path.join(folder,'report.json')));
 const roots=['currentWeather','forecastHourly','forecastDaily','airQuality','locationInfo','weatherAlerts'];
 const b=WeatherKit2.decode(new ByteBuffer(original),roots),a=WeatherKit2.decode(new ByteBuffer(mapped),roots);
 assert.equal(mapped.length,original.length);
 assert.ok(Math.abs(a.currentWeather.temperature-snapshot.current.temperature)<0.0001);
 assert.equal(a.currentWeather.humidity,Math.round(snapshot.current.humidity*100));
 assert.deepEqual(a.airQuality,b.airQuality);assert.deepEqual(a.locationInfo,b.locationInfo);assert.deepEqual(a.weatherAlerts,b.weatherAlerts);
 selected.push({time:event.time,coordinate:[event.latitude,event.longitude],app:event.app,station:snapshot.location,
  temperature:{apple:b.currentWeather.temperature,cwa:snapshot.current.temperature,returned:a.currentWeather.temperature},
  humidity:{apple:b.currentWeather.humidity,cwa:Math.round(snapshot.current.humidity*100),returned:a.currentWeather.humidity},
  bytes:original.length,fields:report.modifiedFields,skipped:report.skipped,coverage:report.coverage,
  sha256:{original:crypto.createHash('sha256').update(original).digest('hex'),mapped:crypto.createHash('sha256').update(mapped).digest('hex')},verified:true});
 if(event.latitude===22.99){
  fs.mkdirSync(path.join(ROOT,'reports/native-tainan'),{recursive:true});
  for(const f of ['original.bin','mapped.bin','cwa.json','report.json','request.json'])fs.copyFileSync(path.join(folder,f),path.join(ROOT,'reports/native-tainan',f));
 }
}
assert.ok(selected.length>0,'Require a real macOS Weather request');
fs.mkdirSync(path.join(ROOT,'reports'),{recursive:true});
fs.writeFileSync(path.join(ROOT,'reports/native-verification.json'),JSON.stringify(selected,null,2));
console.log(JSON.stringify({verifiedNativeResponses:selected.length,results:selected.map(s=>({time:s.time,station:s.station.stationName,temperature:s.temperature,fields:s.fields,skipped:s.skipped}))},null,2));
