import test from 'node:test';import assert from 'node:assert/strict';import {rainWindow,nwpPressure} from '../weather_math.mjs';
test('exact source intervals concatenate without changing their totals',()=>{
 const rows=[
  {start:0,end:3600,amount:1.25,source:'WRF'},
  {start:3600,end:7200,amount:2.75,source:'WRF'}
 ];
 const result=rainWindow(rows,0,7200);
 assert.equal(result.amount,4);
 assert.equal(result.estimated,false);
 assert.equal(result.segments.length,2);
 assert.equal(result.source,'CWA quantitative precipitation; exact complete source windows');
 assert.deepEqual(result.segments.map(segment=>segment.amount),[1.25,2.75]);
});
test('exact whole interval is preferred over an alternate partition',()=>{
 const rows=[
  {start:0,end:7200,amount:4,source:'WRF'},
  {start:0,end:3600,amount:1,source:'WRF'},
  {start:3600,end:7200,amount:3,source:'WRF'}
 ];
 const result=rainWindow(rows,0,7200);
 assert.equal(result.amount,4);
 assert.equal(result.segments.length,1);
});
test('partial source intervals are never apportioned',()=>{
 assert.deepEqual(rainWindow([{start:0,end:21600,amount:6,source:'WRF'}],0,3600),{});
 assert.deepEqual(rainWindow([{start:0,end:3600,amount:1,source:'WRF'}],0,7200),{});
});
test('different source families cannot be blended into one rain window',()=>{
 const rows=[
  {start:0,end:3600,amount:1,source:'WRF',family:'nwp'},
  {start:3600,end:7200,amount:2,source:'radar',family:'radar'}
 ];
 assert.deepEqual(rainWindow(rows,0,7200),{});
});
test('conflicting duplicate windows and ambiguous partitions are rejected',()=>{
 assert.deepEqual(rainWindow([
  {start:0,end:3600,amount:1,source:'WRF'},
  {start:0,end:3600,amount:2,source:'WRF'}
 ],0,3600),{});
 assert.deepEqual(rainWindow([
  {start:0,end:1800,amount:1,source:'WRF'},
  {start:1800,end:7200,amount:2,source:'WRF'},
  {start:0,end:3600,amount:1,source:'WRF'},
  {start:3600,end:7200,amount:2,source:'WRF'}
 ],0,7200),{});
});
test('initialization cycles cannot be combined',()=>{
 const rows=[
  {start:0,end:3600,amount:1,source:'WRF',family:'nwp',initialTime:100},
  {start:3600,end:7200,amount:2,source:'WRF',family:'nwp',initialTime:200}
 ];
 assert.deepEqual(rainWindow(rows,0,7200),{});
});
test('independent complete groups must agree on the total',()=>{
 const equal=rainWindow([
  {start:0,end:3600,amount:1,source:'A'},
  {start:0,end:3600,amount:1,source:'B'}
 ],0,3600);
 assert.equal(equal.amount,1);
 assert.deepEqual(rainWindow([
  {start:0,end:3600,amount:1,source:'A'},
  {start:0,end:3600,amount:2,source:'B'}
 ],0,3600),{});
});
test('invalid windows and rainfall values do not produce coverage',()=>{
 const invalidRows=[
  {start:NaN,end:3600,amount:1},
  {start:0,end:Infinity,amount:1},
  {start:0,end:0,amount:1},
  {start:0,end:3600,amount:-1},
  {start:0,end:3600,amount:5001}
 ];
 assert.deepEqual(rainWindow(invalidRows,0,3600),{});
 assert.deepEqual(rainWindow([],NaN,3600),{});
 assert.deepEqual(rainWindow([],0,Infinity),{});
 assert.deepEqual(rainWindow([],3600,3600),{});
 assert.equal(rainWindow([{start:0,end:3600,amount:0}],0,3600).amount,0);
});
test('model pressure uses bounded six-hour interpolation',()=>{const p=[{forecastStart:0,pressure:1000},{forecastStart:21600,pressure:1006}];assert.equal(nwpPressure(p,10800),1003);assert.equal(nwpPressure(p,0),1000);assert.equal(nwpPressure(p,-1),undefined);assert.equal(nwpPressure(p,21601),undefined);assert.equal(nwpPressure([{forecastStart:0,pressure:1000},{forecastStart:43200,pressure:1006}],10800),undefined);});
