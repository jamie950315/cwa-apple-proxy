import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {transform,hourFields,hourlyProbability,probabilityWindow,dailyTemperature,condition,dayKey,VERSION} from '../mapper.mjs';
import {Weather,WeatherKit2,ByteBuffer,ConditionCode} from '../vendor/weatherkit-codec.full.mjs';
const info=JSON.parse(fs.readFileSync(new URL('../research/actual-brief.json',import.meta.url)));
const original=new Uint8Array(fs.readFileSync(new URL(`../research/apple-${info.source.id}.bin`,import.meta.url)));
const now=Math.floor(info.source.time),h=Math.floor(now/3600)*3600;
const base={source:'CWA',location:{stationId:'TEST'},current:{temperature:21.2,dewPoint:16.2,humidity:0.73,windSpeed:7.2,windDirection:135,observationTime:now-600},shortTerm:{points:[{forecastStart:h,temperature:20,temperatureApparent:22,dewPoint:17,humidity:.7,windSpeed:7.2},{forecastStart:h+10800,temperature:26,temperatureApparent:28,dewPoint:20,humidity:.85,windSpeed:10.8}],intervals:[{start:h,end:h+10800,weatherText:'陰短暫陣雨',precipitationChance:.7}]},weekly:{points:[],intervals:[]}};
const root=b=>Weather.getRootAsWeather(new ByteBuffer(b));
const approx=(a,b)=>assert.ok(Math.abs(a-b)<0.0001,`${a} != ${b}`);
test('version is release 0.3.2',()=>assert.equal(VERSION,'0.3.2'));
test('current CWA observations retain a coherent source and units',()=>{const {bytes,report}=transform(original,base,now),c=root(bytes).currentWeather();approx(c.temperature(),21.2);assert.equal(c.humidity(),73);approx(c.windSpeed(),7.2);assert.equal(c.windDirection(),135);assert.equal(c.asOf(),now-600);assert.equal(c.conditionCode(),ConditionCode.RAIN);assert.ok(report.coverage.currentFields>=5);assert.equal(c.temperatureApparent(),root(original).currentWeather().temperatureApparent());});
test('hourly exact thermodynamic groups do not invent missing fields',()=>{const p=[{forecastStart:h,temperature:20,dewPoint:15,humidity:.7,windSpeed:3},{forecastStart:h+3600,temperature:21,dewPoint:16,humidity:.7},{forecastStart:h+10800,temperature:23,dewPoint:17,humidity:.7,windSpeed:9}];const v=hourFields(p,h+3600);assert.equal(v.temperature,21);assert.equal(v.windSpeed,undefined);assert.match(v._sources.temperature,/exact/);assert.equal(hourFields(p,h+1800).temperature,undefined);assert.equal(hourFields([{forecastStart:h,temperature:10,dewPoint:20,humidity:.7}],h).temperature,undefined);});
test('forecast never extrapolates and gaps >3h stay Apple',()=>{assert.equal(hourFields(base.shortTerm.points,h-1).temperature,undefined);assert.equal(hourFields(base.shortTerm.points,h+10801).temperature,undefined);assert.equal(hourFields([{forecastStart:h,temperature:10},{forecastStart:h+14400,temperature:20}],h+3600).temperature,undefined);});
test('3h PoP leaves native hourly probabilities unchanged',()=>{assert.equal(hourlyProbability(base.shortTerm.intervals,h).value,undefined);const a=root(transform(original,base,now).bytes).forecastHourly(),b=root(original).forecastHourly();for(let i=0;i<a.hoursLength();i++)assert.equal(a.hours(i).precipitationChance(),b.hours(i).precipitationChance());});
test('only exact forecast values arrive in actual FlatBuffer',()=>{const a=root(transform(original,base,now).bytes).forecastHourly(),b=root(original).forecastHourly();let checked=0;for(let i=0;i<a.hoursLength();i++){let t=a.hours(i);if(t.forecastStart()===h+3600){assert.equal(t.temperature(),b.hours(i).temperature());assert.equal(t.windSpeed(),b.hours(i).windSpeed());checked++;}if(t.forecastStart()===h+10800)approx(t.temperature(),26);}assert.equal(checked,1);});
test('unsupported roots, pressure, radar values stay unchanged',()=>{const bytes=transform(original,base,now).bytes;for(const k of ['airQuality','locationInfo','weatherAlerts','forecastNextHour'])assert.deepEqual(WeatherKit2.decode(new ByteBuffer(bytes),[k]),WeatherKit2.decode(new ByteBuffer(original),[k]));for(const k of ['pressure','visibility','precipitationIntensity','windGust'])assert.equal(root(bytes).currentWeather()[k](),root(original).currentWeather()[k]());});
test('all writes are contained in reported scalar bytes',()=>{const {bytes,report}=transform(original,base,now);assert.equal(bytes.length,original.length);const allowed=new Set(report.changes.flatMap(c=>Array.from({length:c.size},(_,i)=>c.offset+i)));for(let i=0;i<bytes.length;i++)if(bytes[i]!==original[i])assert.ok(allowed.has(i));});
test('06-to-06 extrema never replace 00-to-24 extrema',()=>{const s=structuredClone(base),d=root(original).forecastDaily().days(2),day=d.forecastStart(),start=day+21600;s.weekly.intervals=[{start,end:start+43200,temperatureMax:32,temperatureMin:24},{start:start+43200,end:start+86400,temperatureMax:27,temperatureMin:22}];const result=transform(original,s,now),after=root(result.bytes).forecastDaily().days(2);assert.equal(after.temperatureMax(),d.temperatureMax());assert.equal(after.temperatureMin(),d.temperatureMin());assert.equal(result.report.dailyPeriods.length,0);});
test('partial or non-contiguous day/night extrema retain Apple values',()=>{const s=structuredClone(base),d=root(original).forecastDaily().days(2),start=d.forecastStart()+21600;s.weekly.intervals=[{start,end:start+43200,temperatureMax:45,temperatureMin:10}];let a=root(transform(original,s,now).bytes).forecastDaily().days(2);assert.equal(a.temperatureMax(),d.temperatureMax());s.weekly.intervals.push({start:start+40000,end:start+83200,temperatureMax:45,temperatureMin:10});a=root(transform(original,s,now).bytes).forecastDaily().days(2);assert.equal(a.temperatureMax(),d.temperatureMax());});
test('omitted scalar is inserted and readable by native getter',()=>{const b=Uint8Array.from(original),c=root(b).currentWeather(),v=new DataView(b.buffer),vt=c.bb_pos-v.getInt32(c.bb_pos,true);v.setUint16(vt+78,0,true);const {bytes,report}=transform(b,base,now);assert.ok(report.changes.some(s=>s.field==='current.windDirection'&&s.inserted));assert.equal(root(bytes).currentWeather().windDirection(),135);assert.equal(report.skippedFields,0);});
test('future/outdated/NaN timestamps and malformed bodies rejected',()=>{for(const ts of [now-6000,now+600,NaN])assert.throws(()=>transform(original,{...base,current:{...base.current,observationTime:ts}},now));assert.throws(()=>transform(new Uint8Array(3),base,now));const b=Uint8Array.from(original);new DataView(b.buffer).setUint32(0,0x7fffffff,true);assert.throws(()=>transform(b,base,now));});
test('condition mapping handles unknown, mixed precipitation and clouds',()=>{assert.equal(condition('晴'),ConditionCode.CLEAR);assert.equal(condition('晴時多雲'),ConditionCode.MOSTLY_CLEAR);assert.equal(condition('多雲時晴'),ConditionCode.PARTLY_CLOUDY);assert.equal(condition('雨夾雪'),ConditionCode.WINTRY_MIX);assert.equal(condition('-99'),undefined);assert.equal(condition('unknown'),undefined);});
test('Taiwan date key includes UTC+8 midnight',()=>assert.equal(dayKey(Date.parse('2026-09-11T16:00:00Z')/1000),'2026-09-12'));

test('compatible rain-only totals and type companions are updated together',()=>{
 const s=structuredClone(base);s.current.pressure=1008.5;s.current.visibility=13000;s.current.windGust=20;
 const anchor=s.current.observationTime;s.rain={observationTime:anchor,past1h:1.2,past6h:2.3,past24h:3.4};s.nowcast={start:anchor,end:anchor+3600,amount:4.2};
 const current=WeatherKit2.decode(new ByteBuffer(original),['currentWeather']).currentWeather;
 for(const suffix of ['Previous1h','Previous6h','Previous24h','Next1h'])current['precipitationAmount'+suffix+'ByType']=[{expected:1,expectedSnow:0,maximumSnow:0,minimumSnow:0,precipitationType:'RAIN'}];
 const input=WeatherKit2.encode(new ByteBuffer(original),{currentWeather:current});
 const {bytes,report}=transform(input,s,now),c=root(bytes).currentWeather();approx(c.pressure(),1008.5);approx(c.visibility(),13000);approx(c.windGust(),20);
 for(const [field,vector,want] of [['precipitationAmount1h','precipitationAmountPrevious1hByType',1.2],['precipitationAmount6h','precipitationAmountPrevious6hByType',2.3],['precipitationAmount24h','precipitationAmountPrevious24hByType',3.4],['precipitationAmountNext1h','precipitationAmountNext1hByType',4.2]]){approx(c[field](),want);approx(c[vector](0).expected(),want);}
 assert.equal(c.precipitationIntensity(),root(input).currentWeather().precipitationIntensity());assert.ok(report.sourceCoverage.mixed>0);
});

test('CWA weather alerts rebuild native WeatherKit root while preserving other roots',()=>{const s=structuredClone(base);const t=Math.floor(now);s.requested={latitude:25.09,longitude:121.56};s.weatherAlerts={reportedTime:t,detailsUrl:'https://www.cwa.gov.tw/V8/C/W/Warning.html',attributionUrl:'https://opendata.cwa.gov.tw/',alerts:[{id:'01020304-0506-0708-090a-0b0c0d0e0f10',areaId:'臺北市',areaName:'臺北市',attributionUrl:'https://opendata.cwa.gov.tw/',countryCode:'TW',description:'測試強風特報',token:'test-alert',effectiveTime:t,expireTime:t+3600,issuedTime:t,eventOnsetTime:t,eventEndTime:t+3600,detailsUrl:'https://www.cwa.gov.tw/V8/C/W/Warning.html',phenomenon:'陸上強風',severity:'MODERATE',significance:'ADVISORY',source:'中央氣象署',eventSource:'CWA',urgency:'IMMEDIATE',certainty:'UNKNOWN',importance:'NORMAL',responses:['AVOID'],unknown23:0,unknown24:0,unknown25:0,unknown26:0}]};const before=WeatherKit2.decode(new ByteBuffer(original),['news']).news;const {bytes,report}=transform(original,s,now);assert.notEqual(bytes.length,original.length);assert.equal(report.rebuiltRoots[0].root,'weatherAlerts');const decoded=WeatherKit2.decode(new ByteBuffer(bytes),['weatherAlerts','news']);assert.equal(decoded.weatherAlerts.alerts.length,1);assert.equal(decoded.weatherAlerts.alerts[0].phenomenon,'陸上強風');assert.equal(decoded.weatherAlerts.alerts[0].source,'中央氣象署');assert.deepEqual(decoded.news,before);});

test('probability uses only an exact unambiguous official window',()=>{
 for(const p of [0,.1,.3,.7,.99,1]){
  const rows=[{start:h,end:h+10800,precipitationChance:p}];
  const one=probabilityWindow(rows,h,h+3600),three=probabilityWindow(rows,h,h+10800);
  approx(three.value,p);assert.equal(one.value,undefined);assert.equal(three.estimated,false);
 }
 assert.equal(probabilityWindow([{start:h,end:h+3600,precipitationChance:.5}],h,h+7200).value,undefined);
 assert.equal(probabilityWindow([{start:h,end:h+43200,precipitationChance:.6},{start:h,end:h+10800,precipitationChance:.5}],h,h+43200).value,.6);
 assert.equal(probabilityWindow([{start:h,end:h+3600,precipitationChance:.3},{start:h,end:h+3600,precipitationChance:.4}],h,h+3600).value,undefined);
});
test('current CWA astronomy times are written to calendar-matching native days',()=>{
 const s=structuredClone(base),d=root(original).forecastDaily().days(2),key=dayKey(d.forecastStart());
 s.astronomy={days:[{date:key,sunrise:d.forecastStart()+20000,sunset:d.forecastStart()+64000,moonrise:d.forecastStart()+25000}]};
 const a=root(transform(original,s,now).bytes).forecastDaily().days(2);
 assert.equal(a.sunrise(),d.forecastStart()+20000);assert.equal(a.sunset(),d.forecastStart()+64000);assert.equal(a.moonrise(),d.forecastStart()+25000);
});
test('expansion preserves newer opaque root slot 28 byte-for-byte',()=>{
 const s=structuredClone(base),input=Uint8Array.from(original),c=root(input).currentWeather(),v=new DataView(input.buffer),vt=c.bb_pos-v.getInt32(c.bb_pos,true);v.setUint16(vt+72,0,true);const result=transform(input,s,now);
 function item(b){const v=new DataView(b.buffer,b.byteOffset,b.byteLength),r=v.getUint32(0,true),vt=r-v.getInt32(r,true),off=v.getUint16(vt+28,true),target=r+off+v.getUint32(r+off,true),tv=target-v.getInt32(target,true),size=v.getUint16(tv+2,true);return b.slice(target,target+size);}
 assert.deepEqual(item(result.bytes),item(input));approx(root(result.bytes).currentWeather().temperatureDewPoint(),16.2);
});
test('full calendar-day samples update extrema and occurrence times atomically',()=>{
 const s=structuredClone(base),day=root(original).forecastDaily().days(2),start=day.forecastStart();
 s.shortTerm.points=Array.from({length:24},(_,i)=>({forecastStart:start+i*3600,temperature:20+i%8,humidity:.7,dewPoint:15}));
 const result=transform(original,s,now),after=root(result.bytes).forecastDaily().days(2);
 assert.equal(after.temperatureMax(),27);assert.equal(after.temperatureMin(),20);assert.equal(after.temperatureMaxTime(),start+7*3600);assert.equal(after.temperatureMinTime(),start);
 assert.ok(result.report.dailyPeriods.every(x=>x.start===x.appleStart&&x.end===x.appleEnd&&x.estimated));
 s.shortTerm.points.splice(12,1);const missing=root(transform(original,s,now).bytes).forecastDaily().days(2);assert.equal(missing.temperatureMax(),day.temperatureMax());assert.equal(missing.temperatureMaxTime(),day.temperatureMaxTime());
});
test('today uses observed extrema and only remaining exact hourly samples',()=>{
 const start=Date.parse('2026-09-20T00:00:00+08:00')/1000,end=start+86400,t=start+13*3600+600;
 const obs={date:'2026-09-20',start,end,observationTime:t,temperatureMax:32,temperatureMin:24,temperatureMaxTime:start+11*3600,temperatureMinTime:start+5*3600};
 const pts=Array.from({length:24},(_,i)=>({forecastStart:start+i*3600,temperature:i<14?45:25}));
 const result=dailyTemperature(pts,obs,start,end,t+30);assert.equal(result.temperatureMax,32);assert.equal(result.temperatureMaxTime,obs.temperatureMaxTime);assert.equal(result.temperatureMin,24);
 assert.equal(dailyTemperature(pts,{...obs,temperatureMinTime:start-1},start,end,t+30),null);
 assert.equal(dailyTemperature(pts,null,start,end,t+30),null);
 assert.equal(dailyTemperature(pts,obs,start+21600,end+21600,t+30),null);
});
test('unsupported phase companions and source timestamps retain the Apple rain group',()=>{
 const s=structuredClone(base),anchor=s.current.observationTime;const current=WeatherKit2.decode(new ByteBuffer(original),['currentWeather']).currentWeather;
 current.precipitationAmountNext6hByType=[{expected:2,expectedSnow:2,maximumSnow:3,minimumSnow:1,precipitationType:'SNOW'}];
 const input=WeatherKit2.encode(new ByteBuffer(original),{currentWeather:current});s.nwp={initialTime:anchor,rainIntervals:[{start:anchor,end:anchor+21600,amount:6}]};s.rain={observationTime:anchor-600,past1h:99};
 const result=transform(input,s,now),a=root(result.bytes).currentWeather(),b=root(input).currentWeather();assert.equal(a.precipitationAmountNext6h(),b.precipitationAmountNext6h());assert.equal(a.precipitationAmountNext6hByType(0).expected(),b.precipitationAmountNext6hByType(0).expected());assert.equal(a.precipitationAmount1h(),b.precipitationAmount1h());
 assert.ok(result.report.retainedApple.some(x=>x.reason.includes('phase')||x.reason.includes('snow')));
});
test('unchanged official values count as source assignments, not only changed bytes',()=>{
 const current=root(original).currentWeather(),s=structuredClone(base);s.current={temperature:current.temperature(),humidity:current.humidity()/100,dewPoint:current.temperatureDewPoint(),observationTime:now-600};
 const result=transform(original,s,now);assert.ok(result.report.assignments.some(x=>x.field==='current.temperature'));assert.ok(!result.report.changes.some(x=>x.field==='current.temperature'));
});
test('top-level snow phase prevents a daily rain-only companion override',()=>{
 const s=structuredClone(base),daily=WeatherKit2.decode(new ByteBuffer(original),['forecastDaily']).forecastDaily,day=daily.days[2];
 day.precipitationType='SNOW';day.snowfallAmount=0;day.precipitationAmountByType=[{expected:1,expectedSnow:0,maximumSnow:0,minimumSnow:0,precipitationType:'RAIN'}];
 const input=WeatherKit2.encode(new ByteBuffer(original),{forecastDaily:daily});s.nwp={initialTime:day.forecastStart,rainIntervals:[{start:day.forecastStart,end:day.forecastEnd,amount:7}]};
 const before=root(input).forecastDaily().days(2),after=root(transform(input,s,now).bytes).forecastDaily().days(2);
 assert.equal(after.precipitationAmount(),before.precipitationAmount());assert.equal(after.precipitationAmountByType(0).expected(),before.precipitationAmountByType(0).expected());
});
test('nonzero hourly snow intensity preserves the precipitation group',()=>{
 const s=structuredClone(base),hourly=WeatherKit2.decode(new ByteBuffer(original),['forecastHourly']).forecastHourly,hour=hourly.hours.find(x=>x.forecastStart>=now),index=hourly.hours.indexOf(hour);
 hour.precipitationType='RAIN';hour.snowfallAmount=0;hour.snowfallIntensity=2.5;
 const input=WeatherKit2.encode(new ByteBuffer(original),{forecastHourly:hourly});s.nowcast={start:hour.forecastStart,end:hour.forecastStart+3600,amount:4};
 const before=root(input).forecastHourly().hours(index),after=root(transform(input,s,now).bytes).forecastHourly().hours(index);
 assert.equal(after.precipitationAmount(),before.precipitationAmount());assert.equal(after.precipitationIntensity(),before.precipitationIntensity());assert.equal(after.snowfallIntensity(),2.5);
 hour.snowfallIntensity=0;const compatible=WeatherKit2.encode(new ByteBuffer(original),{forecastHourly:hourly});
 const allowed=transform(compatible,s,now);assert.equal(root(allowed.bytes).forecastHourly().hours(index).precipitationAmount(),4);assert.equal(allowed.report.assignments.find(x=>x.field===`hour[${index}].precipitationIntensity`).kind,'mixed');
});
test('incoherent current thermodynamics retain the full Apple thermodynamic group',()=>{
 const s=structuredClone(base);s.current.dewPoint=40;
 const before=root(original).currentWeather(),after=root(transform(original,s,now).bytes).currentWeather();
 for(const k of ['temperature','humidity','temperatureDewPoint','asOf'])assert.equal(after[k](),before[k]());
});
test('interval averages cannot bypass the exact-hour thermodynamic gate',()=>{
 const s=structuredClone(base);s.shortTerm.points=[];s.shortTerm.intervals=[{start:h,end:h+10800,temperature:55,humidity:.9,dewPoint:40}];
 const a=root(transform(original,s,now).bytes).forecastHourly(),b=root(original).forecastHourly();for(let i=0;i<a.hoursLength();i++)assert.equal(a.hours(i).temperature(),b.hours(i).temperature());
});
test('CWA warning unavailability preserves the Apple warning root',()=>{
 const s=structuredClone(base);s.weatherAlerts=null;
 assert.deepEqual(WeatherKit2.decode(new ByteBuffer(transform(original,s,now).bytes),['weatherAlerts']),WeatherKit2.decode(new ByteBuffer(original),['weatherAlerts']));
});
