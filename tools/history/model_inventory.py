from pathlib import Path
import json
import eccodes as ec
R=Path('/home/jamie/cwa-weather-proxy');out=[]
with (R/'research/M-A0064-006.grb2').open('rb') as f:
 while True:
  pos=f.tell();g=ec.codes_grib_new_from_file(f)
  if g is None:break
  keys=['shortName','name','units','typeOfLevel','level','dataDate','dataTime','startStep','endStep','stepUnits','stepType','validityDate','validityTime','gridType','numberOfPoints','Ni','Nj']
  row={'offset':pos,'length':ec.codes_get_message_size(g)}
  for k in keys:
   try:row[k]=ec.codes_get(g,k)
   except Exception:pass
  out.append(row);ec.codes_release(g)
(R/'research/model-inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
summary=[d for d in out if d.get('typeOfLevel') in ['surface','heightAboveGround','meanSea','entireAtmosphere','atmosphere'] and (d.get('level',0)<11 or d.get('typeOfLevel')!='heightAboveGround')]
(R/'research/model-surface-summary.json').write_text(json.dumps({'messages':len(out),'surface':summary},ensure_ascii=False,indent=2))
