import subprocess,json,sys,time,shlex
from pathlib import Path
ROOT=Path(__file__).resolve().parent
mode=sys.argv[1] if len(sys.argv)>1 else 'inspect'
script=r'''
import subprocess,json,time,os
T='/Applications/Tailscale.app/Contents/MacOS/Tailscale'
mode=MODE
r={'mode':mode,'startedAt':time.time()}
def run(args,timeout=35):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout);return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
r['prefsBefore']=json.loads(run([T,'debug','prefs'])['stdout'])
r['prefsBefore']={k:r['prefsBefore'].get(k) for k in ['ExitNodeID','ExitNodeIP','RouteAll','CorpDNS']}
if mode=='cold':
 r['stopWeather']=run(['osascript','-e','tell application "Weather" to quit'])
 for name in ['weatherd','WeatherWidget']:
  r['stop-'+name]=run(['killall','-u','jamie',name])
 time.sleep(2)
 r['start']=run(['open','-a','Weather'])
 time.sleep(20)
r['connections']=run(['sh','-c','lsof -nP -iTCP -iUDP | grep -E "Weather|weatherd|networkse"'])
r['processes']=run(['sh','-c','ps -axo pid,user,comm | grep -E "Weather|weatherd|networkserviceproxy|nesessionmanager"'])
r['log']=run(['/usr/bin/log','show','--last','3m','--info','--debug','--style','compact','--predicate','process == "Weather" OR process == "weatherd" OR process == "networkserviceproxy"'])
lines=r['log']['stdout'].splitlines()
terms=['quic','tether','tthr','relay','17.','proxy','TLS','weatherkit','error','failed','privacy','masque']
r['log']['stdout']='\n'.join(l for l in lines if any(t.lower() in l.lower() for t in terms))[-50000:]
r['routeDefault']=run(['route','-n','get','1.1.1.1'])
r['finishedAt']=time.time()
print(json.dumps(r,ensure_ascii=False,indent=2))
'''.replace('MODE',repr(mode))
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','jamie@100.122.163.78','python3','-'],input=script,capture_output=True,text=True,timeout=115)
(ROOT/f'mac-{mode}.json').write_text(p.stdout)
(ROOT/f'mac-{mode}.stderr').write_text(p.stderr)
print('exit',p.returncode,'bytes',len(p.stdout))
