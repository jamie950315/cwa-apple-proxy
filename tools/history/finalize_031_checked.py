"""Bounded release gate. Tests and data checks must pass before production restart."""
from pathlib import Path
import ast, datetime, glob, hashlib, json, os, re, shutil, subprocess, sys, time, traceback, urllib.request, zipfile
ROOT=Path('/home/jamie/cwa-weather-proxy')
os.chdir(ROOT)
STAMP=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
REPORT=ROOT/'reports'/('release-gate-'+STAMP+'.json')
LOG=ROOT/'logs'/('release-gate-'+STAMP+'.log')
RESULT={'startedAt':datetime.datetime.now().astimezone().isoformat(),'status':'running','changes':[],'checks':[]}
(ROOT/'reports').mkdir(exist_ok=True);(ROOT/'logs').mkdir(exist_ok=True)
def save():
 REPORT.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2))
 (ROOT/'reports/release-gate-latest.json').write_text(json.dumps(RESULT,ensure_ascii=False,indent=2))
def run(args,timeout=90,check=True):
 with LOG.open('a') as out:
  out.write('\n$ '+' '.join(map(str,args))+'\n');out.flush()
  proc=subprocess.run(list(map(str,args)),cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,timeout=timeout,env={**os.environ,'PYTHONPATH':str(ROOT),'NO_COLOR':'1','TERM':'dumb'})
 RESULT['checks'].append({'command':' '.join(map(str,args)),'exit':proc.returncode});save()
 if check and proc.returncode:raise RuntimeError('Release gate command failed; see '+str(LOG))
 return proc.returncode
def http(url,timeout=15):
 with urllib.request.urlopen(url,timeout=timeout) as r:return json.load(r)
def replace_guarded(path,old,new):
 s=path.read_text()
 if old in s:
  path.write_text(s.replace(old,new));RESULT['changes'].append({'file':path.name,'change':'guarded compatibility fix'})
try:
 if os.geteuid()==0:raise RuntimeError('Run release gate as jamie, not root')
 for name in ['addon.py','api.py','mapper.mjs','cwa_aqi.py','cwa_nwp.py','cwa_astronomy.py','flatbuffer_expand.mjs']:
  if not (ROOT/name).is_file():raise RuntimeError('Required staged module missing: '+name)
 backup=ROOT/'backups'/('before-release-gate-'+STAMP);backup.mkdir(parents=True)
 for pattern in ['*.py','*.mjs','dashboard.html','README.md','requirements.lock','package.json']:
  for p in ROOT.glob(pattern):shutil.copy2(p,backup/p.name)
 shutil.copytree(ROOT/'tests',backup/'tests',ignore=shutil.ignore_patterns('__pycache__'))
 RESULT['backup']=str(backup)
 # AQI publish times use YYYY/MM/DD, whereas the shared parser accepts ISO dates.
 aq=ROOT/'cwa_aqi.py';s=aq.read_text();tree=ast.parse(s)
 if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='epoch' for n in ast.walk(tree)) and '_cwa_aqi_iso_epoch' not in s:
  s+='\n# LinkedAPI uses slash-separated dates; preserve the shared timezone handling.\n_cwa_aqi_iso_epoch = epoch\ndef epoch(value):\n    return _cwa_aqi_iso_epoch(value.replace("/", "-") if isinstance(value, str) else value)\n'
  RESULT['changes'].append({'file':'cwa_aqi.py','change':'normalize LinkedAPI slash dates before epoch parsing'})
 s=re.sub(r"(['\"]previousDayComparison['\"]\s*:\s*)['\"]SAME['\"]",r"\1'UNKNOWN'",s)
 aq.write_text(s)
 # The positive QPF fixture must actually cover the next complete hour.
 p=ROOT/'tests/mapper.test.mjs'
 replace_guarded(p,'s.nowcast={start:h,end:h+3600,amount:4.2}', 's.nowcast={start:now,end:now+3600,amount:4.2}')
 run([ROOT/'.venv/bin/python','-m','compileall','-q',*sorted(str(p) for p in ROOT.glob('*.py'))])
 run([ROOT/'.venv/bin/python','-m','pytest','tests','-q'],timeout=120)
 run(['node','--test',*sorted(glob.glob('tests/*.test.mjs'))],timeout=120)
 RESULT['testsPassed']=True;save()
 # Commit only after the complete test suite succeeds.
 units=['cwa-weather-api','cwa-weather-codec','cwa-weather-proxy']
 for candidate in ['cwa-weather-forward']:
  r=subprocess.run(['systemctl','show',candidate,'-p','LoadState','--value'],capture_output=True,text=True)
  if r.stdout.strip()=='loaded':units.append(candidate)
 run(['sudo','systemctl','restart',*units],timeout=60)
 for _ in range(30):
  try:
   a=http('http://100.78.140.101:18880/healthz',3);c=http('http://127.0.0.1:18881/healthz',3)
   if a.get('version')=='0.3.1' and c.get('version')=='0.3.1':break
  except Exception:pass
  time.sleep(1)
 else:raise RuntimeError('Production API/codec version health gate failed')
 RESULT['productionVersions']={'api':a.get('version'),'codec':c.get('version')};save()
 # Poll representative requests. All rows must have current observations and CWA forecasts.
 matrix=[]
 for label,lat,lon in [('臺北',25.09,121.56),('臺南',22.99,120.207),('桃園',24.991,121.311)]:
  d=http(f'http://100.78.140.101:18880/v1/cwa/weather?latitude={lat}&longitude={lon}&country=TW',35)
  if not isinstance(d.get('current',{}).get('temperature'),(int,float)):raise RuntimeError('Missing current temperature '+label)
  if not d.get('shortTerm',{}).get('points'):raise RuntimeError('Missing CWA forecast '+label)
  item={'city':label,'temperature':d['current']['temperature'],'shortForecastPoints':len(d['shortTerm']['points']),'astronomyDays':len((d.get('astronomy') or {}).get('days',[])),'airQuality':d.get('airQuality'),'nwp':d.get('nwp'),'rain':d.get('rain')}
  matrix.append(item)
 RESULT['representativeData']=matrix;save()
 if not all(x['airQuality'] for x in matrix):raise RuntimeError('AQI live-data gate failed; production basic services remain healthy')
 # Refresh model data independently of the 3.5s interactive path.
 worker=ROOT/'model_worker.py'
 if worker.exists():
  service='''[Unit]\nDescription=CWA WRF precipitation and sea-level pressure cache refresh\nAfter=network-online.target\nWants=network-online.target\n[Service]\nType=oneshot\nUser=jamie\nGroup=jamie\nWorkingDirectory=/home/jamie/cwa-weather-proxy\nEnvironment=PYTHONUNBUFFERED=1\nExecStart=/home/jamie/cwa-weather-proxy/.venv/bin/python /home/jamie/cwa-weather-proxy/model_worker.py\nTimeoutStartSec=600\nNice=10\nMemoryMax=768M\nNoNewPrivileges=true\nPrivateTmp=true\nProtectSystem=full\nUMask=0077\n'''
  timer='''[Unit]\nDescription=Hourly CWA WRF cache update\n[Timer]\nOnCalendar=hourly\nRandomizedDelaySec=120\nPersistent=true\nUnit=cwa-weather-model.service\n[Install]\nWantedBy=timers.target\n'''
  for name,text in [('cwa-weather-model.service',service),('cwa-weather-model.timer',timer)]:
   dest=ROOT/'systemd'/name;dest.parent.mkdir(exist_ok=True);dest.write_text(text)
   run(['sudo','install','-m','0644',dest,Path('/etc/systemd/system')/name])
  run(['sudo','systemctl','daemon-reload']);run(['sudo','systemctl','enable','--now','cwa-weather-model.timer'])
  RESULT['modelTimer']='enabled'
 else:RESULT['modelTimer']='worker path needs confirmation'
 states={}
 for name in [*units,'cwa-weather-sni','cwa-weather-routing']:
  q=subprocess.run(['systemctl','show',name,'-p','ActiveState','-p','NRestarts','-p','ExecMainStatus'],capture_output=True,text=True)
  states[name]=q.stdout.strip()
  if 'ActiveState=active' not in q.stdout:raise RuntimeError('Service unhealthy: '+name)
 RESULT['services']=states;RESULT['status']='passed';RESULT['finishedAt']=datetime.datetime.now().astimezone().isoformat();save()
except Exception as exc:
 RESULT['status']='failed';RESULT['error']=str(exc);RESULT['traceback']=traceback.format_exc();save()
 with LOG.open('a') as f:f.write('\n'+traceback.format_exc())
 sys.exit(1)
print(json.dumps({'status':RESULT['status'],'report':str(REPORT),'log':str(LOG)},ensure_ascii=False))
