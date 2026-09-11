from pathlib import Path
R=Path('/home/jamie/cwa-weather-proxy');p=R/'tests/mapper.test.mjs';s=p.read_text().replace("'0.3.0'","'0.3.1'").replace('release 0.3.0','release 0.3.1')
s=s.replace("assert.ok(report.skipped.some(s=>s.field==='current.windDirection'));assert.equal(root(bytes).currentWeather().windDirection(),0);", "assert.ok(report.changes.some(s=>s.field==='current.windDirection'&&s.inserted));assert.equal(root(bytes).currentWeather().windDirection(),135);assert.equal(report.skippedFields,0);")
s=s.replace("missing scalar is reported and buffer stays valid", "omitted scalar is inserted and readable by native getter")
s=s.replace('hourFields,hourlyProbability,condition','hourFields,hourlyProbability,probabilityWindow,condition')
s+='''
test('probability estimates preserve complete interval survival, endpoints, and coverage gaps',()=>{
 for(const p of [0,.1,.3,.7,.99,1]){
  const rows=[{start:h,end:h+10800,precipitationChance:p}];
  const one=probabilityWindow(rows,h,h+3600),three=probabilityWindow(rows,h,h+10800);
  approx(three.value,p);approx(1-(1-one.value)**3,p);assert.equal(one.estimated,true);
 }
 assert.equal(probabilityWindow([{start:h,end:h+3600,precipitationChance:.5}],h,h+7200).value,undefined);
});
test('current CWA astronomy times are written to calendar-matching native days',()=>{
 const s=structuredClone(base),d=root(original).forecastDaily().days(2),key=dayKey(d.forecastStart());
 s.astronomy={days:[{date:key,sunrise:d.forecastStart()+20000,sunset:d.forecastStart()+64000,moonrise:d.forecastStart()+25000}]};
 const a=root(transform(original,s,now).bytes).forecastDaily().days(2);
 assert.equal(a.sunrise(),d.forecastStart()+20000);assert.equal(a.sunset(),d.forecastStart()+64000);assert.equal(a.moonrise(),d.forecastStart()+25000);
});
test('expansion preserves newer opaque root slot 28 byte-for-byte',()=>{
 const s=structuredClone(base);s.rain={past1h:3.21,past6h:8.65};const result=transform(original,s,now);
 function item(b){const v=new DataView(b.buffer,b.byteOffset,b.byteLength),r=v.getUint32(0,true),vt=r-v.getInt32(r,true),off=v.getUint16(vt+28,true),target=r+off+v.getUint32(r+off,true),tv=target-v.getInt32(target,true),size=v.getUint16(tv+2,true);return b.slice(target,target+size);}
 assert.deepEqual(item(result.bytes),item(original));approx(root(result.bytes).currentWeather().precipitationAmount1h(),3.21);approx(root(result.bytes).currentWeather().precipitationAmount6h(),8.65);
});
test('CWA warning unavailability preserves the Apple warning root',()=>{
 const s=structuredClone(base);s.weatherAlerts=null;
 assert.deepEqual(WeatherKit2.decode(new ByteBuffer(transform(original,s,now).bytes),['weatherAlerts']),WeatherKit2.decode(new ByteBuffer(original),['weatherAlerts']));
});
'''
p.write_text(s)
p=R/'tests/test_addon.py';p.write_text(p.read_text().replace("startswith('0.3.0')","startswith('0.3.1')"))
