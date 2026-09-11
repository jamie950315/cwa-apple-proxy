import eccodes as ec,json
from pathlib import Path
R=Path('/home/jamie/cwa-weather-proxy');inv=json.loads((R/'research/model-inventory.json').read_text());out=[]
with (R/'research/M-A0064-006.grb2').open('rb') as f:
 for item in inv[60:]:
  f.seek(item['offset']);g=ec.codes_grib_new_from_file(f);row={}
  for k in ['shortName','name','units','discipline','parameterCategory','parameterNumber','tablesVersion','localTablesVersion','typeOfLevel','level','startStep','endStep','stepType','centre','missingValue','minimum','maximum']:
   try:row[k]=ec.codes_get(g,k)
   except Exception:pass
  try:row['taipei']=ec.codes_grib_find_nearest(g,25.09,121.56,npoints=1)
  except Exception as e:row['sampleError']=type(e).__name__
  out.append(row);ec.codes_release(g)
(R/'research/grib-parameters.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
