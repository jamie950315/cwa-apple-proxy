from pathlib import Path
import subprocess,json,time,shutil,os
ROOT=Path('/home/jamie/cwa-weather-proxy');OUT=ROOT/'research/no-exit'
commands=[]
def run(args,timeout=60):
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
 commands.append({'command':args,'exit':p.returncode,'stdout':p.stdout[-16000:],'stderr':p.stderr[-6000:]})
 if p.returncode:raise RuntimeError('Command failed: '+args[0])
 return p.stdout
report={'startedAt':int(time.time()),'checks':commands}
try:
 run([str(ROOT/'.venv/bin/python'),'-m','pytest','tests','-q'])
 run(['node','--test',*[str(p) for p in (ROOT/'tests').glob('*.test.mjs')]])
 old=Path('/etc/systemd/system/cwa-weather-routing.service')
 backup=Path((OUT/'transport-backup.txt').read_text())
 shutil.copy2(old,backup/'cwa-weather-routing.service')
 run(['sudo',str(ROOT/'.venv/bin/python'),'split_routes.py','apply'])
 for name in ['cwa-weather-routing.service','cwa-weather-route-status.service','cwa-weather-route-status.timer']:
  run(['sudo','install','-m','0644',str(ROOT/'systemd'/name),'/etc/systemd/system/'+name])
 run(['sudo','systemctl','daemon-reload'])
 run(['sudo',str(ROOT/'.venv/bin/python'),'bridgectl.py','apply'])
 run(['sudo','systemctl','enable','--now','cwa-weather-route-status.timer'])
 run(['sudo','systemctl','start','cwa-weather-route-status.service'])
 run(['sudo','systemctl','restart','cwa-weather-api'])
 time.sleep(2)
 run(['curl','-fsS','--max-time','8','http://100.78.140.101:18880/healthz'])
 run(['curl','-fsS','--max-time','8','http://127.0.0.1:18881/healthz'])
 run(['systemctl','is-active','AdGuardHome','cwa-weather-api','cwa-weather-proxy','cwa-weather-sni','cwa-weather-routing','cwa-weather-route-status.timer'])
 report['result']='deployed'
 report['splitRoutes']=json.loads(run([str(ROOT/'.venv/bin/python'),'split_routes.py','status']))
except Exception as e:
 report['result']='failed';report['error']=type(e).__name__+': '+str(e)
finally:
 report['finishedAt']=int(time.time());(OUT/'activation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(report['result'])
