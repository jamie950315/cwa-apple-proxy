from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/tests/test_addon.py');s=p.read_text().replace("startswith('0.2.0')","startswith('0.3.0')");p.write_text(s)
p=Path('/home/jamie/cwa-weather-proxy/tests/mapper.test.mjs');s=p.read_text();s=s.replace("import {transform,hourFields,condition,dayKey,VERSION}","import {transform,hourFields,hourlyProbability,condition,dayKey,VERSION}");s=s.replace("version is release 0.2.0',()=>assert.equal(VERSION,'0.2.0')","version is release 0.3.0',()=>assert.equal(VERSION,'0.3.0')")
old="test('3h PoP is never substituted for 1h PoP',()=>{const b=root(original).forecastHourly(),a=root(transform(original,base,now).bytes).forecastHourly();for(let i=0;i<b.hoursLength();i++)assert.equal(a.hours(i).precipitationChance(),b.hours(i).precipitationChance());});"
new="test('3h PoP is split to aggregate-preserving hourly PoP',()=>{const p=hourlyProbability(base.shortTerm.intervals,h);approx(p.value,1-Math.pow(.3,1/3));const a=root(transform(original,base,now).bytes).forecastHourly();let checked=0;for(let i=0;i<a.hoursLength();i++){const x=a.hours(i);if(x.forecastStart()>=h&&x.forecastStart()<h+10800){assert.equal(x.precipitationChance(),Math.round(p.value*100));checked++;}}assert.ok(checked>0);});"
if old not in s:raise SystemExit('old pop test missing')
s=s.replace(old,new);p.write_text(s)
