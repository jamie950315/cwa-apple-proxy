import {WeatherKit2,ByteBuffer,Weather} from '../vendor/weatherkit-codec.full.mjs';
import fs from 'node:fs';
let out={methods:{},empty:{}};
for (const key of ['currentWeather','forecastHourly','forecastDaily']) {
 out.methods[key]=Weather.prototype[key].toString();
 try {
  const b=WeatherKit2.encode(undefined,{[key]:{}});
  out.empty[key]=WeatherKit2.decode(new ByteBuffer(b),[key]);
 }catch(e){out.empty[key]={error:e.message};}
}
fs.writeFileSync('/home/jamie/cwa-weather-proxy/research/codec-shapes.json',JSON.stringify(out,null,2));
