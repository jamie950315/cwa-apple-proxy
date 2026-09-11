import fs from 'node:fs';
import {WeatherKit2,ByteBuffer,Weather} from '../vendor/weatherkit-codec.full.mjs';
const dir='/home/jamie/cwa-weather-proxy/research';
const source=fs.readdirSync(dir).filter(f=>f.startsWith('apple-')&&f.endsWith('.json')).map(f=>JSON.parse(fs.readFileSync(`${dir}/${f}`))).find(r=>r.status===200&&r.query.country?.[0]==='TW');
if(!source)throw Error('No Taiwan capture');
const bytes=new Uint8Array(fs.readFileSync(`${dir}/apple-${source.id}.bin`));
const decoded=WeatherKit2.decode(new ByteBuffer(bytes),['currentWeather','forecastHourly','forecastDaily','locationInfo']);
const root=Weather.getRootAsWeather(new ByteBuffer(bytes));
let methods={};
for(const [key,obj] of Object.entries({current:root.currentWeather(),hour:root.forecastHourly()?.hours(0),day:root.forecastDaily()?.days(0)})){
 if(!obj)continue;methods[key]={};
 for(const name of Object.getOwnPropertyNames(Object.getPrototypeOf(obj)))if(!['constructor','__init'].includes(name))methods[key][name]=obj[name].toString();
}
fs.writeFileSync(`${dir}/actual-decoded.json`,JSON.stringify(decoded,null,2));
fs.writeFileSync(`${dir}/actual-accessors.json`,JSON.stringify(methods,null,2));
fs.writeFileSync(`${dir}/actual-brief.json`,JSON.stringify({source,current:decoded.currentWeather,hour:decoded.forecastHourly?.hours?.[0],hourCount:decoded.forecastHourly?.hours?.length,day:decoded.forecastDaily?.days?.[0],dayCount:decoded.forecastDaily?.days?.length},null,2));
