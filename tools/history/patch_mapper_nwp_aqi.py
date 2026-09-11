from pathlib import Path
R=Path('/home/jamie/cwa-weather-proxy');p=R/'mapper.mjs';s=p.read_text();s="import {rainWindow,nwpPressure} from './weather_math.mjs';\n"+s
s=s.replace("const current=root.currentWeather();", "const nwp=snapshot.nwp||{},nwpPoints=nwp.points||[],rainRows=[...(nwp.rainIntervals||[]),...(qpf?[qpf]:[])],precipitationPeriods=[];\n const current=root.currentWeather();")
s=s.replace("set(current,'precipitationAmountNext1h',qpf?.amount,'current','CWA F-B0046-001 radar QPF direct next-1h amount');", """for(const hours of [1,6,24]){
   const result=rainWindow(rainRows,now,now+hours*3600);
   set(current,'precipitationAmountNext'+hours+'h',result.amount,'current',result.source||'CWA');
   if(Number.isFinite(result.amount))precipitationPeriods.push({field:'current.precipitationAmountNext'+hours+'h',start:now,end:now+hours*3600,segments:result.segments});
  }""")
s=s.replace("const amount=overlapAmount(qpf,ts,ts+3600);set(hour,'precipitationAmount',amount,`hour[${i}]`,'CWA F-B0046-001 QPF apportioned by time overlap');", """const amount=rainWindow(rainRows,ts,ts+3600);
   set(hour,'precipitationAmount',amount.amount,`hour[${i}]`,amount.source||'CWA');
   set(hour,'precipitationIntensity',amount.amount,`hour[${i}]`,'CWA uniform hourly average precipitation rate estimate');
   set(hour,'pressure',nwpPressure(nwpPoints,ts),`hour[${i}]`,'CWA WRF-3km sea-level pressure, <=6h linear interpolation');""")
needle="   const winds=selected.filter(p=>Number.isFinite(p.windSpeed));"
s=s.replace(needle,"""   let quantitative=rainWindow(rainRows,day.forecastStart(),day.forecastEnd());
   if(Number.isFinite(rain.today)&&Number.isFinite(rain.observationTime)&&dayKey(rain.observationTime)===key&&rain.observationTime>day.forecastStart()&&rain.observationTime<day.forecastEnd()){
    const remainder=rainWindow(rainRows,rain.observationTime,day.forecastEnd());
    if(Number.isFinite(remainder.amount))quantitative={...remainder,amount:rain.today+remainder.amount,source:'CWA observed rain since midnight + QPF/WRF forecast remainder; estimate'};
   }
   set(day,'precipitationAmount',quantitative.amount,`day[${i}]`,quantitative.source||'CWA');
   if(Number.isFinite(quantitative.amount))precipitationPeriods.push({field:`day[${i}].precipitationAmount`,start:day.forecastStart(),end:day.forecastEnd(),source:quantitative.source});
"""+needle)
s=s.replace(" if(snapshot.weatherAlerts&&Array.isArray", """ if(snapshot.airQuality&&Number.isFinite(snapshot.airQuality.index)){
  const {provenance,...aqi}=snapshot.airQuality;
  output=WeatherKit2.encode(new ByteBuffer(output),{airQuality:aqi});
  const verify=WeatherKit2.decode(new ByteBuffer(output),['airQuality']).airQuality;
  if(!verify||verify.index!==aqi.index||verify.scale!==aqi.scale)throw Error('CWA AQI root verification failed');
  rebuiltRoots.push({root:'airQuality',index:aqi.index,scale:aqi.scale,source:'CWA LinkedAPI / Taiwan MOENV',provenance});
 }
 if(snapshot.weatherAlerts&&Array.isArray""")
s=s.replace('coverage,dailyPeriods,rebuiltRoots,','coverage,dailyPeriods,precipitationPeriods,rebuiltRoots,')
s=s.replace("'forecast pressure/visibility/gust outside observation'", "'forecast visibility/gust, and pressure beyond validated CWA model coverage'")
s=s.replace("'next-6h/24h precipitation amounts where no continuously available public numeric CWA grid is integrated'", "'quantitative precipitation beyond valid QPF/WRF coverage; missing phase-specific distribution vectors'")
s=s.replace("'air quality root pending authenticated CWA LinkedAPI L-003 integration'", "'air-quality auxiliary comparisons without corresponding CWA observations'")
p.write_text(s)
p=R/'flatbuffer_expand.mjs';s=p.read_text().replace('n.newSize=align(n.newSize,SIZE[p.type]);','n.newSize=align(n.pos+n.newSize,SIZE[p.type])-n.pos;');s=s.replace('cursor=align(cursor,8);n.out=cursor;', 'cursor=align(cursor,8)+(n.pos%8);n.out=cursor;');p.write_text(s)
print('NWP rainfall/pressure and CWA LinkedAPI AQI mapping staged')
