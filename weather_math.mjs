// Time-window conversions with explicit coverage. Uniform within each source
// interval is an assumption; no uncovered portion is implicitly treated as zero.
export function rainWindow(intervals,start,end){
 if(!Number.isFinite(start)||!Number.isFinite(end)||end<=start)return {};
 const rows=(intervals||[]).filter(p=>Number.isFinite(p.start)&&Number.isFinite(p.end)&&p.end>p.start&&p.end>start&&p.start<end&&Number.isFinite(p.amount)&&p.amount>=0&&p.amount<=5000);
 const cuts=[...new Set([start,end,...rows.flatMap(p=>[Math.max(start,p.start),Math.min(end,p.end)])])].sort((a,b)=>a-b);
 let amount=0;const segments=[];
 for(let i=0;i<cuts.length-1;i++){
  const a=cuts[i],b=cuts[i+1];if(b<=a)continue;
  const row=rows.filter(p=>p.start<=a&&p.end>=b).sort((a,b)=>(a.end-a.start)-(b.end-b.start))[0];
  if(!row)return {};
  const part=row.amount*(b-a)/(row.end-row.start);amount+=part;
  segments.push({start:a,end:b,amount:part,sourceStart:row.start,sourceEnd:row.end,source:row.source});
 }
 return {amount,segments,estimated:true,source:'CWA QPF/WRF quantitative precipitation; uniform rate within source windows; full coverage required'};
}
export function nwpPressure(points,ts){
 const rows=(points||[]).filter(p=>Number.isFinite(p.forecastStart)&&Number.isFinite(p.pressure)&&p.pressure>=850&&p.pressure<=1100).sort((a,b)=>a.forecastStart-b.forecastStart);
 let a,b;
 for(const row of rows){if(row.forecastStart===ts)return row.pressure;if(row.forecastStart<ts)a=row;else{b=row;break;}}
 if(!a||!b||b.forecastStart-a.forecastStart>21600)return undefined;
 return a.pressure+(b.pressure-a.pressure)*(ts-a.forecastStart)/(b.forecastStart-a.forecastStart);
}
