from pathlib import Path
import subprocess,json,time
ROOT=Path('/home/jamie/cwa-weather-proxy');OUT=ROOT/'research/no-exit'
script=r'''
import subprocess,json,time
T='/Applications/Tailscale.app/Contents/MacOS/Tailscale'
def run(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=15);return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
p=json.loads(run([T,'debug','prefs'])['stdout'])
r={'time':int(time.time()),'preferences':{k:p.get(k) for k in ['ExitNodeID','ExitNodeIP','RouteAll','CorpDNS']},'defaultRoute':run(['route','-n','get','1.1.1.1']),'relayRoute':run(['route','-n','get','17.253.87.61']),'proxy':run(['scutil','--proxy']),'dns':{}}
for ns in ['100.78.140.101','100.91.87.20','100.116.187.43','100.100.100.100']:
 r['dns'][ns]=run(['dig','@'+ns,'weatherkit.apple.com','A','+short','+time=3','+tries=1'])
print(json.dumps(r,ensure_ascii=False,indent=2))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','jamie@100.122.163.78','python3','-'],input=script,capture_output=True,text=True,timeout=95)
(OUT/'mac-final.stderr').write_text(p.stderr)
if p.returncode:raise RuntimeError('Mac SSH failed: '+str(p.returncode))
r=json.loads(p.stdout);(OUT/'mac-final.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
a=json.loads((OUT/'mac-acceptance.json').read_text())
rows=[]
for line in (ROOT/'logs/bridge-reverse.jsonl').read_text().splitlines():
 try:
  d=json.loads(line)
  if a['coldStartAt']<=d.get('time',0)<=r['time'] and d.get('status')=='modified':rows.append(d)
 except ValueError:pass
out={'time':r['time'],'noExitAtStart':a['checks']['noExitNode'],'noExitAtEnd':not r['preferences'].get('ExitNodeID') and not r['preferences'].get('ExitNodeIP'),'generalTrafficDirect':'interface: en0' in r['defaultRoute']['stdout'],'nativeAppResponses':sum('Weather_macOS' in x.get('app','') for x in rows),'nativeWidgetResponses':sum('WeatherWidget_macOS' in x.get('app','') for x in rows),'latestNativeResponses':rows[-5:],'dnsEachServer':{k:v['stdout'].strip() for k,v in r['dns'].items()},'relayPublicRouteStillDirect':'interface: en0' in r['relayRoute']['stdout']}
(OUT/'final-network-evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
