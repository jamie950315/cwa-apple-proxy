from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/flatbuffer_expand.mjs');s=p.read_text();s=s.replace("node.references.push({off,target});\n   if(body.includes('__indirect'))", "node.references.push({off,target});\n   if(pos===dv.getUint32(0,true)&&!['currentWeather','forecastHourly','forecastDaily'].includes(name))continue;\n   if(body.includes('__indirect'))")
s=s.replace("check(tp,4);const child=table(t[name](i));", "try{check(tp,4);}catch(e){throw Error(`Expansion vector ${name}[${i}]/${count} at ${target} target ${tp}`)}const child=table(t[name](i));")
p.write_text(s)
