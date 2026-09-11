from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/mapper.mjs');s=p.read_text()
s=s.replace("import {Weather,ByteBuffer,ConditionCode} from './vendor/weatherkit-codec.full.mjs';","import {Weather,WeatherKit2,ByteBuffer,ConditionCode} from './vendor/weatherkit-codec.full.mjs';")
old=""" const affected=new Set(changes.flatMap(c=>Array.from({length:c.size},(_,j)=>c.offset+j)));for(let i=0;i<bytes.length;i++)if(bytes[i]!==original[i]&&!affected.has(i))throw Error('Unexpected byte change');
 return {bytes,report:{version:VERSION,modifiedFields:changes.length,skippedFields:skipped.length,changes,skipped,coverage,dailyPeriods,observation:snapshot.location,observationTime:snapshot.current.observationTime,policy:'CWA-first: observations + analyzed temperature + rain gauges + 1h radar QPF + township forecast; probabilities are time-resolution-aware derivations where Apple and CWA windows differ',preserved:['cloud-cover percentages','forecast pressure/visibility/gust outside observation','next-6h/24h precipitation amounts where no continuously available public numeric CWA grid is available','air quality/alerts roots pending schema-level root replacement','astronomy pending current-year CWA table validation','Apple-specific news/historical-comparison/change products','unknown FlatBuffers slots']}};
}"""
new=""" const affected=new Set(changes.flatMap(c=>Array.from({length:c.size},(_,j)=>c.offset+j)));for(let i=0;i<bytes.length;i++)if(bytes[i]!==original[i]&&!affected.has(i))throw Error('Unexpected byte change');
 const rebuiltRoots=[];let output=bytes;
 if(snapshot.weatherAlerts&&Array.isArray(snapshot.weatherAlerts.alerts)){
  const a=snapshot.weatherAlerts,reported=Number.isFinite(a.reportedTime)?a.reportedTime:now;
  const obj={metadata:{attributionUrl:a.attributionUrl||'https://opendata.cwa.gov.tw/',expireTime:now+300,language:'zh-TW',latitude:snapshot.requested?.latitude,longitude:snapshot.requested?.longitude,providerLogo:null,providerName:'中央氣象署',readTime:now,reportedTime:reported,temporarilyUnavailable:false,sourceType:'STATION'},detailsUrl:a.detailsUrl||'https://www.cwa.gov.tw/V8/C/W/Warning.html',alerts:a.alerts};
  output=WeatherKit2.encode(new ByteBuffer(bytes),{weatherAlerts:obj});
  const verify=WeatherKit2.decode(new ByteBuffer(output),['weatherAlerts']).weatherAlerts;
  if(!verify||verify.alerts.length!==obj.alerts.length)throw Error('WeatherAlerts root verification failed');
  rebuiltRoots.push({root:'weatherAlerts',items:obj.alerts.length,source:'CWA W-C0033-002'});
 }
 return {bytes:output,report:{version:VERSION,modifiedFields:changes.length,skippedFields:skipped.length,changes,skipped,coverage,dailyPeriods,rebuiltRoots,bufferBytesBefore:original.length,bufferBytesAfter:output.length,observation:snapshot.location,observationTime:snapshot.current.observationTime,policy:'CWA-first: observations + analyzed temperature + rain gauges + 1h radar QPF + township forecast + CWA alerts; probabilities are time-resolution-aware derivations where Apple and CWA windows differ',preserved:['cloud-cover percentages where no current public operational grid is integrated','forecast pressure/visibility/gust outside observation','next-6h/24h precipitation amounts where no continuously available public numeric CWA grid is integrated','air quality root pending authenticated CWA LinkedAPI L-003 integration','astronomy pending current-year CWA table validation','Apple-specific news/historical-comparison/change products','unknown FlatBuffers slots']}};
}"""
if old not in s:raise SystemExit('mapper tail missing')
p.write_text(s.replace(old,new))
