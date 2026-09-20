import {rainWindow,nwpPressure} from './weather_math.mjs';
import {expandScalars} from './flatbuffer_expand.mjs';
import {Weather,WeatherKit2,ByteBuffer,ConditionCode} from './vendor/weatherkit-codec.full.mjs';
export const VERSION='0.3.2';
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
  const exact=points.filter(p=>p.forecastStart===ts&&Number.isFinite(p[field]));
  if(exact.length&&exact.every(p=>p[field]===exact[0][field])){out[field]=exact[0][field];sources[field]='CWA official exact forecast point';}
 }
 if(!(Number.isFinite(out.temperature)&&Number.isFinite(out.humidity)&&Number.isFinite(out.dewPoint)&&out.temperature>=-60&&out.temperature<=65&&out.humidity>=0&&out.humidity<=1&&out.dewPoint<=out.temperature+1e-6))
  for(const k of ['temperature','humidity','dewPoint','temperatureApparent']){delete out[k];delete sources[k];}
 return {...out,_sources:sources};
}
// Only the source's exact event window is an official probability. Marginals
// cannot identify hourly probabilities or the union of correlated rain events.
export function probabilityWindow(intervals,start,end){
 if(!Number.isFinite(start)||!Number.isFinite(end)||end<=start)return {};
 const rows=(intervals||[]).filter(p=>p.start===start&&p.end===end&&Number.isFinite(p.precipitationChance)&&p.precipitationChance>=0&&p.precipitationChance<=1);
 if(!rows.length||rows.some(p=>p.precipitationChance!==rows[0].precipitationChance))return {};
 return {value:rows[0].precipitationChance,source:'CWA official matching precipitation interval',sourceIntervals:[{start,end,sourceProbability:rows[0].precipitationChance}],estimated:false};
}
export function hourlyProbability(intervals,ts){return probabilityWindow(intervals,ts,ts+3600);}
function dayProbability(intervals,start,end){return probabilityWindow(intervals,start,end);}
export function dailyTemperature(points,observed,start,end,now){
 if(!Number.isFinite(start)||!Number.isFinite(end)||end-start!==86400||(start+28800)%86400!==0||end<=now)return null;
 const rows=[];let first=start;let usesObserved=false;
 if(start<now){
  if(!observed||observed.start!==start||observed.end!==end||observed.date!==dayKey(start)||!Number.isFinite(observed.observationTime)||observed.observationTime>now||now-observed.observationTime>5400)return null;
  const {temperatureMin:lo,temperatureMax:hi,temperatureMinTime:lt,temperatureMaxTime:ht}=observed;
  if(![lo,hi,lt,ht].every(Number.isFinite)||lo>hi||lo<-60||hi>65||lt<start||ht<start||lt>observed.observationTime||ht>observed.observationTime)return null;
  rows.push({temperature:lo,time:lt},{temperature:hi,time:ht});first=Math.floor(observed.observationTime/3600)*3600+3600;usesObserved=true;
 }
 for(let t=first;t<end;t+=3600){
  const candidates=(points||[]).filter(p=>p.forecastStart===t&&Number.isFinite(p.temperature)&&p.temperature>=-60&&p.temperature<=65);
  if(!candidates.length||candidates.some(p=>p.temperature!==candidates[0].temperature))return null;
  const p=candidates[0];if(Number.isFinite(p.dewPoint)&&p.dewPoint>p.temperature+1e-6)return null;
  rows.push({temperature:p.temperature,time:t});
 }
 if(!rows.length)return null;
 const low=rows.reduce((a,b)=>b.temperature<a.temperature?b:a),high=rows.reduce((a,b)=>b.temperature>a.temperature?b:a);
 return {temperatureMin:low.temperature,temperatureMax:high.temperature,temperatureMinTime:low.time,temperatureMaxTime:high.time,start,end,estimated:true,source:usesObserved?'CWA observed daily extremes + remaining exact hourly forecast samples; derived calendar-day extrema':'CWA exact hourly forecast samples; derived calendar-day extrema'};
}
export function transform(original,snapshot,now=Math.floor(Date.now()/1000)){
 if(!(original instanceof Uint8Array)||original.length<12||original.length>4000000)throw Error('Invalid FlatBuffer size');
 if(snapshot?.source!=='CWA'||!Number.isFinite(snapshot.current?.temperature)||!Number.isFinite(snapshot.current?.observationTime))throw Error('Missing CWA observation');
 if(now-snapshot.current.observationTime>5400||snapshot.current.observationTime-now>300)throw Error('Stale observation');
 const bytes=Uint8Array.from(original),bb=new ByteBuffer(bytes),view=new DataView(bytes.buffer);
 const rp=view.getUint32(0,true);if(rp<4||rp>=bytes.length-4)throw Error('Invalid root offset');
 const root=Weather.getRootAsWeather(bb),changes=[],skipped=[],pending=new Map(),assignments=[],retainedApple=[],coverage={currentFields:0,hoursMapped:0,daysMapped:0,interpolatedFields:0,precipitationFields:0};
 const retain=(field,reason)=>retainedApple.push({field,reason});
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
  assignments.push({field:label+'.'+field,source,kind:source.includes('Apple')?'mixed':/derived|derivation|estimate|interpolation/i.test(source)?'derived':'official'});
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
  const coherent=Number.isFinite(values.temperature)&&Number.isFinite(values.humidity)&&Number.isFinite(values.dewPoint)&&values.temperature>=-60&&values.temperature<=65&&values.humidity>=0&&values.humidity<=1&&values.dewPoint<=values.temperature+1e-6;
  if(coherent){
   for(const k of ['temperature','temperatureApparent'])set(table,k,values[k],label,source(k));
   set(table,'humidity',values.humidity*100,label,source('humidity'));set(table,'temperatureDewPoint',values.dewPoint,label,source('dewPoint'));
  }else retain(label+'.thermodynamicGroup','no complete coherent same-time CWA group');
  for(const k of ['windSpeed','windDirection','windGust','uvIndex','visibility','pressure'])set(table,k,values[k],label,source(k));
  set(table,'conditionCode',condition(values.weatherText),label,values.conditionSource||source('weatherText'));
  return coherent;
 }
 function rainGroup(table,field,amount,label,source,vectorName=field+'ByType',hourly=false){
  if(!Number.isFinite(amount))return false;
  if(amount<0||amount>5000||typeof table?.[field]!=='function')return false;
  const snow=field.replace('precipitation','snowfall');
  if(typeof table[snow]==='function'&&table[snow]()!==0){retain(label+'.'+field,'Apple snow companion has no CWA phase equivalent');return false;}
  if(typeof table.precipitationType==='function'&&table.precipitationType()!==1){retain(label+'.'+field,'top-level Apple phase is not rain-only');return false;}
  if(hourly){
   // RAIN=1 in the pinned native codec. Retain its classification; do not infer
   // a new phase from temperature or manufacture snow/distribution bounds.
   if(table.precipitationType?.()!==1||table.snowfallIntensity?.()!==0){retain(label+'.'+field,'no existing Apple rain-only phase or nonzero snow intensity');return false;}
  }else{
   const count=table[vectorName+'Length']?.();
   if(count===0&&amount===0&&table[field]()===0){set(table,field,amount,label,source);return true;}
   if(count!==1){retain(label+'.'+field,'missing or multi-phase Apple companion; no fabricated phase split');return false;}
   const type=table[vectorName](0);validateTable(type);
   if(type.precipitationType?.()!==1||['expectedSnow','maximumSnow','minimumSnow'].some(k=>typeof type[k]!=='function'||type[k]()!==0)){
    retain(label+'.'+field,'unsupported Apple phase or snow distribution');return false;
   }
   set(type,'expected',amount,label+'.'+vectorName+'[0]',source+'; retained Apple rain-only phase');
  }
  set(table,field,amount,label,source+'; retained Apple rain-only phase');
  if(hourly)set(table,'precipitationIntensity',amount,label,source+'; derived mean rate over the exact one-hour forecast window; retained Apple rain-only phase');
  return true;
 }
 const points=snapshot.shortTerm?.points||[],shortIntervals=snapshot.shortTerm?.intervals||[],weekly=snapshot.weekly?.intervals||[],rain=snapshot.rain||{},qpf=snapshot.nowcast||null;
 const nwp=snapshot.nwp||{},nwpPoints=nwp.points||[],rainRows=[...(nwp.rainIntervals||[]).map(p=>({...p,family:'wrf',initialTime:nwp.initialTime})),...(qpf?[{...qpf,family:'qpf',initialTime:qpf.start}]:[])],precipitationPeriods=[];
 const current=root.currentWeather();
 if(current){
  validateTable(current);if(!Number.isFinite(current.temperature())||Math.abs(current.temperature())>100)throw Error('Unknown current weather layout');
  const values={...snapshot.current,_sources:{...(snapshot.current._sources||{})}};
  if(!values.weatherText){values.weatherText=intervalFields(shortIntervals,now).weatherText;values.conditionSource='CWA forecast interval';}
  const coherent=fields(current,values,'current');if(coherent)set(current,'asOf',snapshot.current.observationTime,'current','CWA observation time');
  const anchor=coherent?snapshot.current.observationTime:current.asOf();
  for(const hours of [1,6,24]){
   const field='precipitationAmount'+hours+'h';
   if(rain.observationTime===anchor)rainGroup(current,field,rain['past'+hours+'h'],'current','CWA rain gauge exact trailing '+hours+'h window','precipitationAmountPrevious'+hours+'hByType');
   else if(Number.isFinite(rain['past'+hours+'h']))retain('current.'+field,'rain observation time differs from current asOf');
  }
  retain('current.precipitationIntensity','ten-minute average is not instantaneous intensity');
  for(const hours of [1,6,24]){
   const result=rainWindow(rainRows,anchor,anchor+hours*3600),field='precipitationAmountNext'+hours+'h';
   if(rainGroup(current,field,result.amount,'current',result.source||'CWA'))precipitationPeriods.push({field:'current.'+field,start:anchor,end:anchor+hours*3600,segments:result.segments});
   else if(!Number.isFinite(result.amount))retain('current.'+field,'no exact complete CWA source window');
  }
  coverage.currentFields=changes.length;
 }
 const hourly=root.forecastHourly();
 if(hourly){
  validateTable(hourly);const count=hourly.hoursLength();if(count>1000)throw Error('Unknown hourly layout');
  for(let i=0;i<count;i++){
   const hour=hourly.hours(i);validateTable(hour);const ts=hour.forecastStart();if(ts<now-3600)continue;const before=changes.length;
   fields(hour,{weatherText:intervalFields(shortIntervals,ts).weatherText,...hourFields(points,ts)},`hour[${i}]`);
   const pop2=hourlyProbability([...shortIntervals,...weekly],ts);
   if(Number.isFinite(pop2.value))set(hour,'precipitationChance',pop2.value*100,`hour[${i}]`,pop2.source);
   else retain(`hour[${i}].precipitationChance`,'no exact official CWA probability window');
   const amount=rainWindow(rainRows,ts,ts+3600);
   rainGroup(hour,'precipitationAmount',amount.amount,`hour[${i}]`,amount.source||'CWA',undefined,true);
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
   const before=changes.length,selected=weekly.filter(p=>dayKey(p.start)===key),extremes=dailyTemperature(points,snapshot.dailyObservedExtremes,day.forecastStart(),day.forecastEnd(),now);
   if(extremes&&['temperatureMax','temperatureMin','temperatureMaxTime','temperatureMinTime'].every(k=>typeof day[k]==='function')){
    for(const k of ['temperatureMax','temperatureMin','temperatureMaxTime','temperatureMinTime'])set(day,k,extremes[k],`day[${i}]`,extremes.source);
    dailyPeriods.push({date:key,start:extremes.start,end:extremes.end,appleStart:day.forecastStart(),appleEnd:day.forecastEnd(),estimated:true,source:extremes.source});
   }else{
    retain(`day[${i}].temperatureExtrema`,'no full same-calendar-day hourly coverage and observed extrema with occurrence times');
   }
   const uv=selected.filter(p=>Number.isFinite(p.uvIndex));if(uv.length)set(day,'maxUvIndex',Math.max(...uv.map(p=>p.uvIndex)),`day[${i}]`,'CWA daytime UV forecast');
   const daytime=selected.find(p=>p.weatherText&&new Date((p.start+28800)*1000).getUTCHours()===6);if(daytime)set(day,'conditionCode',condition(daytime.weatherText),`day[${i}]`,'CWA daytime weather forecast');
   const dp2=dayProbability([...shortIntervals,...weekly],day.forecastStart(),day.forecastEnd());
   if(Number.isFinite(dp2.value))set(day,'precipitationChance',dp2.value*100,`day[${i}]`,dp2.source);
   else retain(`day[${i}].precipitationChance`,'no exact official CWA probability window');
   const quantitative=rainWindow(rainRows,day.forecastStart(),day.forecastEnd());
   if(rainGroup(day,'precipitationAmount',quantitative.amount,`day[${i}]`,quantitative.source||'CWA'))precipitationPeriods.push({field:`day[${i}].precipitationAmount`,start:day.forecastStart(),end:day.forecastEnd(),source:quantitative.source,segments:quantitative.segments});
   const winds=selected.filter(p=>Number.isFinite(p.windSpeed));if(winds.length)set(day,'windSpeedAvg',winds.reduce((s,p)=>s+p.windSpeed,0)/winds.length,`day[${i}]`,'CWA mean of available day/night wind forecasts');
   for(const name of ['daytimeForecast','overnightForecast','restOfDayForecast']){
    const part=day[name]?.();if(!part)continue;validateTable(part);const matches=weekly.filter(p=>p.start===part.forecastStart()&&p.end===part.forecastEnd());if(!matches.length)continue;
    const v=Object.assign({},...matches),label=`day[${i}].${name}`;fields(part,v,label);
    // CWA period extrema do not supply occurrence times. Retain the complete
    // Apple extrema family instead of mixing CWA values with Apple's times.
    const pop=probabilityWindow(matches,part.forecastStart(),part.forecastEnd());
    if(Number.isFinite(pop.value))set(part,'precipitationChance',pop.value*100,label,pop.source);
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
 const sourceCoverage={official:0,derived:0,mixed:0};for(const a of assignments)sourceCoverage[a.kind]++;
 return {bytes:output,report:{version:VERSION,modifiedFields:changes.length,skippedFields:skipped.length,changes,skipped,coverage,sourceCoverage,assignments,retainedApple,dailyPeriods,precipitationPeriods,rebuiltRoots,bufferBytesBefore:original.length,bufferBytesAfter:output.length,observation:snapshot.location,observationTime:snapshot.current.observationTime,policy:'CWA aligned-source policy: coherent station thermodynamics, exact hourly points and probability windows, complete rainfall windows with compatible companions, and explicitly derived calendar-day extrema with occurrence times; unsupported groups retain Apple',preserved:['unmatched hourly/daily precipitation probabilities and fractional rainfall windows','rainfall with missing or incompatible Apple phase companions','incomplete calendar-day extrema or thermodynamic groups','cloud-cover percentages where no current public operational grid is integrated','forecast visibility/gust, and pressure beyond validated CWA model coverage','air-quality auxiliary comparisons without corresponding CWA observations','moon phase/illumination and nautical/astronomical twilight where CWA time tables contain no equivalent','Apple-specific news/historical-comparison/change products','unknown FlatBuffers slots']}};
}
