import {rainWindow,nwpPressure} from './weather_math.mjs';
import {expandScalars} from './flatbuffer_expand.mjs';
import {Weather,WeatherKit2,ByteBuffer,ConditionCode} from './vendor/weatherkit-codec.full.mjs';
export const VERSION='0.3.1';
const TYPES={Int8:[1,-128,127],Uint8:[1,0,255],Int16:[2,-32768,32767],Uint16:[2,0,65535],Int32:[4,-2147483648,2147483647],Uint32:[4,0,4294967295],Float32:[4,-3.4e38,3.4e38],Float64:[8,-Number.MAX_VALUE,Number.MAX_VALUE]};
const NUMERIC=['temperature','temperatureApparent','dewPoint','humidity','windSpeed'];
export function condition(text){
 if(typeof text!=='string'||!text||text==='-99')return undefined;
 if(text.includes('雷'))return text.includes('局部')?ConditionCode.ISOLATED_THUNDERSTORMS:ConditionCode.THUNDERSTORMS;
 if(text.includes('雨')&&text.includes('雪'))return ConditionCode.WINTRY_MIX;
 if(text.includes('雪'))return ConditionCode.SNOW;
 if(text.includes('大雨')||text.includes('豪雨'))return ConditionCode.HEAVY_RAIN;
 if(text.includes('雨'))return ConditionCode.RAIN;
 if(text.includes('霧'))return ConditionCode.FOGGY;
 if(text.includes('霾'))return ConditionCode.HAZE;
 if(text.includes('陰'))return text.startsWith('多雲')?ConditionCode.MOSTLY_CLOUDY:ConditionCode.CLOUDY;
 if(text.includes('多雲'))return text.startsWith('晴')?ConditionCode.MOSTLY_CLEAR:text.includes('晴')?ConditionCode.PARTLY_CLOUDY:ConditionCode.MOSTLY_CLOUDY;
 if(text.includes('晴'))return ConditionCode.CLEAR;
 return undefined;
}
export function dayKey(ts){return new Date((ts+28800)*1000).toISOString().slice(0,10);}
export function intervalFields(intervals,ts){const out={};for(const p of intervals||[])if(p.start<=ts&&ts<p.end)Object.assign(out,p);return out;}
export function hourFields(points,ts){
 const out={},sources={};
 for(const field of [...NUMERIC,'windDirection']){
  const series=points.filter(p=>Number.isFinite(p[field])).sort((a,b)=>a.forecastStart-b.forecastStart);
  const exact=series.find(p=>p.forecastStart===ts);
  if(exact){out[field]=exact[field];sources[field]='CWA forecast point';continue;}
  let a,b;for(const p of series){if(p.forecastStart<ts)a=p;else {b=p;break;}}
  if(!a||!b||b.forecastStart-a.forecastStart>10800)continue;
  if(field==='windDirection')continue;
  const ratio=(ts-a.forecastStart)/(b.forecastStart-a.forecastStart);out[field]=a[field]+ratio*(b[field]-a[field]);sources[field]='CWA linear interpolation <=3h';
 }
 return {...out,_sources:sources};
}
// Estimates require equal precipitation-event hazard over each source interval.
// Probability resolution conversion adds a model assumption; provenance states it.
export function probabilityWindow(intervals,start,end){
 if(!Number.isFinite(start)||!Number.isFinite(end)||end<=start)return {};
 const rows=(intervals||[]).filter(p=>Number.isFinite(p.start)&&Number.isFinite(p.end)&&p.end>p.start&&p.end>start&&p.start<end&&Number.isFinite(p.precipitationChance)&&p.precipitationChance>=0&&p.precipitationChance<=1);
 const cuts=[...new Set([start,end,...rows.flatMap(p=>[Math.max(start,p.start),Math.min(end,p.end)])])].sort((a,b)=>a-b);
 let logSurvival=0;const selected=[];
 for(let i=0;i<cuts.length-1;i++){
  const a=cuts[i],b=cuts[i+1];if(b<=a)continue;
  const p=rows.filter(p=>p.start<=a&&p.end>=b).sort((a,b)=>(a.end-a.start)-(b.end-b.start))[0];
  if(!p)return {};
  logSurvival+=Math.log1p(-p.precipitationChance)*(b-a)/(p.end-p.start);
  selected.push({sourceStart:p.start,sourceEnd:p.end,sourceProbability:p.precipitationChance,start:a,end:b});
 }
 return {value:-Math.expm1(logSurvival),source:'CWA-derived probability estimate; equal hazard and independent increments assumed; uncalibrated',sourceIntervals:selected,estimated:true};
}
export function hourlyProbability(intervals,ts){return probabilityWindow(intervals,ts,ts+3600);}
function dayProbability(intervals,start,end){return probabilityWindow(intervals,start,end);}
function paired(intervals,key,field){
 const rows=intervals.filter(p=>dayKey(p.start)===key&&Number.isFinite(p[field])).sort((a,b)=>a.start-b.start);
 const unique=rows.filter((p,i)=>i===0||p.start!==rows[i-1].start||p.end!==rows[i-1].end);
 if(unique.length!==2||unique[0].end!==unique[1].start||unique[0].end-unique[0].start!==43200||unique[1].end-unique[1].start!==43200)return null;
 return unique;
}
function overlapAmount(qpf,start,end){
 if(!qpf||!Number.isFinite(qpf.amount)||!Number.isFinite(qpf.start)||!Number.isFinite(qpf.end)||qpf.end<=qpf.start)return undefined;
 const seconds=Math.max(0,Math.min(end,qpf.end)-Math.max(start,qpf.start));
 return seconds>0?qpf.amount*seconds/(qpf.end-qpf.start):undefined;
}
export function transform(original,snapshot,now=Math.floor(Date.now()/1000)){
 if(!(original instanceof Uint8Array)||original.length<12||original.length>4000000)throw Error('Invalid FlatBuffer size');
 if(snapshot?.source!=='CWA'||!Number.isFinite(snapshot.current?.temperature)||!Number.isFinite(snapshot.current?.observationTime))throw Error('Missing CWA observation');
 if(now-snapshot.current.observationTime>5400||snapshot.current.observationTime-now>300)throw Error('Stale observation');
 const bytes=Uint8Array.from(original),bb=new ByteBuffer(bytes),view=new DataView(bytes.buffer);
 const rp=view.getUint32(0,true);if(rp<4||rp>=bytes.length-4)throw Error('Invalid root offset');
 const root=Weather.getRootAsWeather(bb),changes=[],skipped=[],pending=new Map(),coverage={currentFields:0,hoursMapped:0,daysMapped:0,interpolatedFields:0,precipitationFields:0};
 function validateTable(table){
  if(!table||!Number.isInteger(table.bb_pos)||table.bb_pos<4||table.bb_pos+4>bytes.length)throw Error('Invalid table position');
  const vt=table.bb_pos-view.getInt32(table.bb_pos,true);if(vt<4||vt+4>bytes.length)throw Error('Invalid vtable position');
  const len=view.getUint16(vt,true),size=view.getUint16(vt+2,true);if(len<4||len%2||vt+len>bytes.length||size<4||table.bb_pos+size>bytes.length)throw Error('Invalid table bounds');return {vt,len,size};
 }
 validateTable(root);
 function set(table,field,value,label,source='CWA'){
  if(!table||typeof table[field]!=='function'||!Number.isFinite(value))return;
  const layout=validateTable(table),getter=table[field].toString(),match=getter.match(/__offset\(this\.bb_pos,(\d+)\)/),type=getter.match(/\.read(Uint8|Int8|Uint16|Int16|Uint32|Int32|Float32|Float64)\(/)?.[1];
  if(!match||!TYPES[type])throw Error('Unsupported scalar '+field);
  const [size,lo,hi]=TYPES[type];if(value<lo||value>hi)throw Error('Out of range '+field);if(!type.startsWith('Float'))value=Math.round(value);
  const before=table[field]();if(before===value)return;
  const index=Number(match[1]),offset=index<layout.len?view.getUint16(layout.vt+index,true):0;
  if(!offset){pending.set(table.bb_pos+':'+index,{tablePos:table.bb_pos,index,type,value,before,field:label+'.'+field,source});return;}
  const pos=table.bb_pos+offset;if(offset<4||offset+size>layout.size||pos+size>bytes.length)throw Error('Scalar bounds');
  view['set'+type](pos,value,true);changes.push({field:label+'.'+field,before,after:table[field](),offset:pos,size,source});
  if(source.includes('interpolation'))coverage.interpolatedFields++;
  if(field.toLowerCase().includes('precipitation'))coverage.precipitationFields++;
 }
 function fields(table,values,label){
  const source=k=>values._sources?.[k]||'CWA';
  for(const k of ['temperature','temperatureApparent','windSpeed','windDirection','windGust','uvIndex','visibility','pressure'])set(table,k,values[k],label,source(k));
  set(table,'humidity',values.humidity===undefined?undefined:values.humidity*100,label,source('humidity'));set(table,'temperatureDewPoint',values.dewPoint,label,source('dewPoint'));set(table,'conditionCode',condition(values.weatherText),label,values.conditionSource||source('weatherText'));
 }
 const points=snapshot.shortTerm?.points||[],shortIntervals=snapshot.shortTerm?.intervals||[],weekly=snapshot.weekly?.intervals||[],rain=snapshot.rain||{},qpf=snapshot.nowcast||null;
 const nwp=snapshot.nwp||{},nwpPoints=nwp.points||[],rainRows=[...(nwp.rainIntervals||[]),...(qpf?[qpf]:[])],precipitationPeriods=[];
 const current=root.currentWeather();
 if(current){
  validateTable(current);if(!Number.isFinite(current.temperature())||Math.abs(current.temperature())>100)throw Error('Unknown current weather layout');
  const forecast=hourFields(points,now),values={...snapshot.current,_sources:{...(snapshot.current._sources||{})}};
  if(Number.isFinite(forecast.temperatureApparent)){values.temperatureApparent=forecast.temperatureApparent;values._sources.temperatureApparent=forecast._sources.temperatureApparent;}
  if(!Number.isFinite(values.dewPoint)&&Number.isFinite(forecast.dewPoint)){values.dewPoint=forecast.dewPoint;values._sources.dewPoint=forecast._sources.dewPoint;}
  if(!values.weatherText){values.weatherText=intervalFields(shortIntervals,now).weatherText;values.conditionSource='CWA forecast interval';}
  fields(current,values,'current');set(current,'asOf',snapshot.current.observationTime,'current','CWA observation time');
  set(current,'precipitationAmount1h',rain.past1h,'current','CWA O-A0002-001 rain gauge Past1hr');
  set(current,'precipitationAmount6h',rain.past6h,'current','CWA O-A0002-001 rain gauge Past6Hr');
  set(current,'precipitationAmount24h',rain.past24h,'current','CWA O-A0002-001 rain gauge Past24hr');
  set(current,'precipitationIntensity',rain.intensity,'current','CWA rain gauge Past10Min × 6 hourly-rate estimate');
  for(const hours of [1,6,24]){
   const result=rainWindow(rainRows,now,now+hours*3600);
   set(current,'precipitationAmountNext'+hours+'h',result.amount,'current',result.source||'CWA');
   if(Number.isFinite(result.amount))precipitationPeriods.push({field:'current.precipitationAmountNext'+hours+'h',start:now,end:now+hours*3600,segments:result.segments});
  }
  coverage.currentFields=changes.length;
 }
 const hourly=root.forecastHourly();
 if(hourly){
  validateTable(hourly);const count=hourly.hoursLength();if(count>1000)throw Error('Unknown hourly layout');
  for(let i=0;i<count;i++){
   const hour=hourly.hours(i);validateTable(hour);const ts=hour.forecastStart();if(ts<now-3600)continue;const before=changes.length;
   fields(hour,{...intervalFields(shortIntervals,ts),...hourFields(points,ts)},`hour[${i}]`);
   const pop2=hourlyProbability([...shortIntervals,...weekly],ts);
   set(hour,'precipitationChance',Number.isFinite(pop2.value)?pop2.value*100:undefined,`hour[${i}]`,pop2.source||'CWA');
   const amount=rainWindow(rainRows,ts,ts+3600);
   set(hour,'precipitationAmount',amount.amount,`hour[${i}]`,amount.source||'CWA');
   set(hour,'precipitationIntensity',amount.amount,`hour[${i}]`,'CWA uniform hourly average precipitation rate estimate');
   set(hour,'pressure',nwpPressure(nwpPoints,ts),`hour[${i}]`,'CWA WRF-3km sea-level pressure, <=6h linear interpolation');
   if(changes.length>before)coverage.hoursMapped++;
  }
 }
 const daily=root.forecastDaily(),dailyPeriods=[];
 if(daily){
  validateTable(daily);if(daily.daysLength()>40)throw Error('Unknown daily layout');
  for(let i=0;i<daily.daysLength();i++){
   const day=daily.days(i);validateTable(day);const key=dayKey(day.forecastStart());if(day.forecastEnd()<now)continue;
   const astro=snapshot.astronomy?.days?.find(p=>p.date===key);
   if(astro)for(const k of ['sunrise','sunset','solarNoon','sunriseCivil','sunsetCivil','moonrise','moonset'])set(day,k,astro[k],`day[${i}]`,astro._sources?.[k]||'CWA calendar astronomy');
   const before=changes.length,selected=weekly.filter(p=>dayKey(p.start)===key),highs=paired(weekly,key,'temperatureMax'),lows=paired(weekly,key,'temperatureMin');
   if(highs&&lows&&highs[0].start===lows[0].start&&highs[1].end===lows[1].end){
    const max=Math.max(...highs.map(p=>p.temperatureMax)),min=Math.min(...lows.map(p=>p.temperatureMin));if(min<=max){set(day,'temperatureMax',max,`day[${i}]`,'CWA complete day/night maximum');set(day,'temperatureMin',min,`day[${i}]`,'CWA complete day/night minimum');dailyPeriods.push({date:key,start:highs[0].start,end:highs[1].end,appleStart:day.forecastStart(),appleEnd:day.forecastEnd()});}
   }
   const uv=selected.filter(p=>Number.isFinite(p.uvIndex));if(uv.length)set(day,'maxUvIndex',Math.max(...uv.map(p=>p.uvIndex)),`day[${i}]`,'CWA daytime UV forecast');
   const daytime=selected.find(p=>p.weatherText&&new Date((p.start+28800)*1000).getUTCHours()===6);if(daytime)set(day,'conditionCode',condition(daytime.weatherText),`day[${i}]`,'CWA daytime weather forecast');
   const dp2=dayProbability([...shortIntervals,...weekly],day.forecastStart(),day.forecastEnd());set(day,'precipitationChance',Number.isFinite(dp2.value)?dp2.value*100:undefined,`day[${i}]`,dp2.source||'CWA');
   let quantitative=rainWindow(rainRows,day.forecastStart(),day.forecastEnd());
   if(Number.isFinite(rain.today)&&Number.isFinite(rain.observationTime)&&dayKey(rain.observationTime)===key&&rain.observationTime>day.forecastStart()&&rain.observationTime<day.forecastEnd()){
    const remainder=rainWindow(rainRows,rain.observationTime,day.forecastEnd());
    if(Number.isFinite(remainder.amount))quantitative={...remainder,amount:rain.today+remainder.amount,source:'CWA observed rain since midnight + QPF/WRF forecast remainder; estimate'};
   }
   set(day,'precipitationAmount',quantitative.amount,`day[${i}]`,quantitative.source||'CWA');
   if(Number.isFinite(quantitative.amount))precipitationPeriods.push({field:`day[${i}].precipitationAmount`,start:day.forecastStart(),end:day.forecastEnd(),source:quantitative.source});
   const winds=selected.filter(p=>Number.isFinite(p.windSpeed));if(winds.length)set(day,'windSpeedAvg',winds.reduce((s,p)=>s+p.windSpeed,0)/winds.length,`day[${i}]`,'CWA mean of available day/night wind forecasts');
   for(const name of ['daytimeForecast','overnightForecast','restOfDayForecast']){
    const part=day[name]?.();if(!part)continue;validateTable(part);const matches=weekly.filter(p=>p.start===part.forecastStart()&&p.end===part.forecastEnd());if(!matches.length)continue;
    const v=Object.assign({},...matches),label=`day[${i}].${name}`;fields(part,v,label);for(const k of ['temperatureMin','temperatureMax','temperatureApparentMin','temperatureApparentMax'])set(part,k,v[k],label,'CWA matching forecast interval');set(part,'precipitationChance',v.precipitationChance===undefined?undefined:v.precipitationChance*100,label,'CWA official matching precipitation interval');
   }
   if(changes.length>before)coverage.daysMapped++;
  }
 }
 const affected=new Set(changes.flatMap(c=>Array.from({length:c.size},(_,j)=>c.offset+j)));for(let i=0;i<bytes.length;i++)if(bytes[i]!==original[i]&&!affected.has(i))throw Error('Unexpected byte change');
 const rebuiltRoots=[];let output=bytes;
 if(pending.size){
  const expanded=expandScalars(bytes,[...pending.values()]);output=expanded.bytes;
  changes.push(...expanded.insertions);
  for(const p of expanded.insertions){if(p.field.startsWith('current.'))coverage.currentFields++;if(p.field.toLowerCase().includes('precipitation'))coverage.precipitationFields++;}
  rebuiltRoots.push({root:'omittedScalarExpansion',insertedFields:expanded.insertions.length,prefixBytes:expanded.prefixBytes,clonedTables:expanded.clonedTables,preservesOriginalPayload:true});
 }

 if(snapshot.airQuality&&Number.isFinite(snapshot.airQuality.index)){
  const {provenance,...aqi}=snapshot.airQuality;
  output=WeatherKit2.encode(new ByteBuffer(output),{airQuality:aqi});
  const verify=WeatherKit2.decode(new ByteBuffer(output),['airQuality']).airQuality;
  if(!verify||verify.index!==aqi.index||verify.scale!==aqi.scale)throw Error('CWA AQI root verification failed');
  rebuiltRoots.push({root:'airQuality',index:aqi.index,scale:aqi.scale,source:'CWA LinkedAPI / Taiwan MOENV',provenance});
 }
 if(snapshot.weatherAlerts&&Array.isArray(snapshot.weatherAlerts.alerts)){
  const a=snapshot.weatherAlerts,reported=Number.isFinite(a.reportedTime)?a.reportedTime:now;
  const obj={metadata:{attributionUrl:a.attributionUrl||'https://opendata.cwa.gov.tw/',expireTime:now+300,language:'zh-TW',latitude:snapshot.requested?.latitude,longitude:snapshot.requested?.longitude,providerLogo:null,providerName:'中央氣象署',readTime:now,reportedTime:reported,temporarilyUnavailable:false,sourceType:'STATION'},detailsUrl:a.detailsUrl||'https://www.cwa.gov.tw/V8/C/W/Warning.html',alerts:a.alerts};
  const upstream=WeatherKit2.decode(new ByteBuffer(output),['weatherAlerts']).weatherAlerts;
  const ids=new Set(obj.alerts.map(p=>p.id));
  obj.alerts=[...(upstream?.alerts||[]).filter(p=>!ids.has(p.id)&&p.eventSource!=='CWA'),...obj.alerts];
  output=WeatherKit2.encode(new ByteBuffer(output),{weatherAlerts:obj});
  const verify=WeatherKit2.decode(new ByteBuffer(output),['weatherAlerts']).weatherAlerts;
  if(!verify||verify.alerts.length!==obj.alerts.length)throw Error('WeatherAlerts root verification failed');
  rebuiltRoots.push({root:'weatherAlerts',items:obj.alerts.length,source:'CWA W-C0033-002'});
 }
 return {bytes:output,report:{version:VERSION,modifiedFields:changes.length,skippedFields:skipped.length,changes,skipped,coverage,dailyPeriods,precipitationPeriods,rebuiltRoots,bufferBytesBefore:original.length,bufferBytesAfter:output.length,observation:snapshot.location,observationTime:snapshot.current.observationTime,policy:'CWA-first: observations + analyzed temperature + rain gauges + 1h radar QPF + township forecast + CWA alerts; probabilities are time-resolution-aware derivations where Apple and CWA windows differ',preserved:['cloud-cover percentages where no current public operational grid is integrated','forecast visibility/gust, and pressure beyond validated CWA model coverage','quantitative precipitation beyond valid QPF/WRF coverage; missing phase-specific distribution vectors','air-quality auxiliary comparisons without corresponding CWA observations','moon phase/illumination and nautical/astronomical twilight where CWA time tables contain no equivalent','Apple-specific news/historical-comparison/change products','unknown FlatBuffers slots']}};
}
