export function rainWindow(intervals,start,end){
 if(!Number.isFinite(start)||!Number.isFinite(end)||end<=start)return {};
 const rows=(Array.isArray(intervals)?intervals:[]).filter(row=>
  row&&Number.isFinite(row.start)&&Number.isFinite(row.end)&&row.end>row.start&&
  row.start>=start&&row.end<=end&&Number.isFinite(row.amount)&&
  row.amount>=0&&row.amount<=5000
 );
 const groups=new Map();
 for(const row of rows){
  const family=row.family??row.source??'';
  const cycle=row.initialTime??'';
  const key=JSON.stringify([family,cycle]);
  if(!groups.has(key))groups.set(key,[]);
  groups.get(key).push(row);
 }

 const candidates=[];
 for(const group of groups.values()){
  const windows=new Map();let conflicting=false;
  for(const row of group){
   const key=`${row.start}\u0000${row.end}`;
   const existing=windows.get(key);
   if(existing&&existing.amount!==row.amount){conflicting=true;break;}
   if(!existing)windows.set(key,row);
  }
  if(conflicting)return {};
  const unique=[...windows.values()];
  const exact=unique.find(row=>row.start===start&&row.end===end);
  if(exact){candidates.push({rows:[exact],exact:true});continue;}

  const byStart=new Map();
  for(const row of unique){
   if(!byStart.has(row.start))byStart.set(row.start,[]);
   byStart.get(row.start).push(row);
  }
  const memo=new Map();
  function coversFrom(cursor){
   if(cursor===end)return {count:1,path:[]};
   if(memo.has(cursor))return memo.get(cursor);
   let count=0,path;
   for(const row of byStart.get(cursor)||[]){
    const suffix=coversFrom(row.end);
    if(!suffix.count)continue;
    count=Math.min(2,count+suffix.count);
    if(!path)path=[row,...suffix.path];
    if(count>1)break;
   }
   const result={count,path};memo.set(cursor,result);return result;
  }
  const coverage=coversFrom(start);
  if(coverage.count>1)return {};
  if(coverage.count===1)candidates.push({rows:coverage.path,exact:false});
 }
 if(!candidates.length)return {};
 const totals=candidates.map(candidate=>candidate.rows.reduce((sum,row)=>sum+row.amount,0));
 if(totals.some(total=>total!==totals[0]))return {};
 const chosen=candidates.find(candidate=>candidate.exact)||candidates[0];
 const segments=chosen.rows.map(row=>({
  start:row.start,end:row.end,amount:row.amount,
  sourceStart:row.start,sourceEnd:row.end,source:row.source
 }));
 return {amount:totals[0],segments,estimated:false,source:'CWA quantitative precipitation; exact complete source windows'};
}
export function nwpPressure(points,ts){
 const rows=(points||[]).filter(p=>Number.isFinite(p.forecastStart)&&Number.isFinite(p.pressure)&&p.pressure>=850&&p.pressure<=1100).sort((a,b)=>a.forecastStart-b.forecastStart);
 let a,b;
 for(const row of rows){if(row.forecastStart===ts)return row.pressure;if(row.forecastStart<ts)a=row;else{b=row;break;}}
 if(!a||!b||b.forecastStart-a.forecastStart>21600)return undefined;
 return a.pressure+(b.pressure-a.pressure)*(ts-a.forecastStart)/(b.forecastStart-a.forecastStart);
}
