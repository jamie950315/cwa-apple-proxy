from pathlib import Path
import shutil,time
r=Path('/home/jamie/cwa-weather-proxy');b=r/'backups'/('v0.3.0-before-expansion-'+str(int(time.time())));b.mkdir()
for p in list(r.glob('*.py'))+list(r.glob('*.mjs'))+list(r.glob('*.html')):shutil.copy2(p,b/p.name)
p=r/'mapper.mjs';s=p.read_text()
s="import {expandScalars} from './flatbuffer_expand.mjs';\n"+s
s=s.replace("VERSION='0.3.0'","VERSION='0.3.1'")
a=s.index('export function hourlyProbability(');z=s.index('function paired(',a)
s=s[:a]+'''// Estimates require equal precipitation-event hazard over each source interval.
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
''' +s[z:]
s=s.replace('changes=[],skipped=[],coverage=', 'changes=[],skipped=[],pending=new Map(),coverage=')
s=s.replace("if(!offset){skipped.push({field:label+'.'+field,reason:'scalar omitted in original FlatBuffer'});return;}","if(!offset){pending.set(table.bb_pos+':'+index,{tablePos:table.bb_pos,index,type,value,before,field:label+'.'+field,source});return;}")
s=s.replace("const pop=hourlyProbability(shortIntervals,ts);const pop2=Number.isFinite(pop.value)?pop:hourlyProbability(weekly,ts);", "const pop2=hourlyProbability([...shortIntervals,...weekly],ts);")
s=s.replace("const dp=dayProbability(shortIntervals,day.forecastStart(),day.forecastEnd());const dp2=Number.isFinite(dp.value)?dp:dayProbability(weekly,day.forecastStart(),day.forecastEnd());", "const dp2=dayProbability([...shortIntervals,...weekly],day.forecastStart(),day.forecastEnd());")
s=s.replace("const rebuiltRoots=[];let output=bytes;", """const rebuiltRoots=[];let output=bytes;
 if(pending.size){
  const expanded=expandScalars(bytes,[...pending.values()]);output=expanded.bytes;
  changes.push(...expanded.insertions);
  for(const p of expanded.insertions){if(p.field.startsWith('current.'))coverage.currentFields++;if(p.field.toLowerCase().includes('precipitation'))coverage.precipitationFields++;}
  rebuiltRoots.push({root:'omittedScalarExpansion',insertedFields:expanded.insertions.length,prefixBytes:expanded.prefixBytes,clonedTables:expanded.clonedTables,preservesOriginalPayload:true});
 }
""")
s=s.replace('WeatherKit2.encode(new ByteBuffer(bytes),{weatherAlerts:obj})','WeatherKit2.encode(new ByteBuffer(output),{weatherAlerts:obj})')
p.write_text(s)
print(b)
