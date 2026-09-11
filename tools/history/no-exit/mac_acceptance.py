from pathlib import Path
import subprocess,json,time
ROOT=Path('/home/jamie/cwa-weather-proxy');OUT=ROOT/'research/no-exit'
script=r'''
import subprocess,json,socket,time
T='/Applications/Tailscale.app/Contents/MacOS/Tailscale'
result={'startedAt':time.time(),'checks':{}}
def run(args,timeout=30):
 p=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
 return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
result['configure']=run([T,'set','--exit-node=','--accept-routes=true','--accept-dns=true'])
prefs=json.loads(run([T,'debug','prefs'])['stdout'])
result['preferences']={k:prefs.get(k) for k in ['ExitNodeID','ExitNodeIP','CorpDNS','RouteAll']}
result['checks']['noExitNode']=not prefs.get('ExitNodeID') and not prefs.get('ExitNodeIP')
result['defaultRoute']=run(['route','-n','get','1.1.1.1'])
result['piRoute']=run(['route','-n','get','100.78.140.101'])
result['relayRoute']=run(['route','-n','get','17.253.87.61'])
result['checks']['generalTrafficDirect']='interface: en0' in result['defaultRoute']['stdout']
result['dns']={}
for ns in ['100.78.140.101','100.100.100.100']:
 vals=[]
 for i in range(3):vals.append(run(['dig','@'+ns,'weatherkit.apple.com','A','+short','+time=3','+tries=1']))
 result['dns'][ns]=vals
result['checks']['weatherDNSPointsToPi']=all('100.78.140.101' in r['stdout'] for values in result['dns'].values() for r in values)
result['genericHTTP']={}
for url in ['https://www.apple.com/','https://www.google.com/','https://pi5.tail19030f.ts.net/','http://100.78.140.101:18880/healthz']:
 result['genericHTTP'][url]=run(['curl','-sS','-o','/dev/null','-w','%{http_code}','--max-time','15',url])
result['checks']['genericHTTPHealthy']=all(v['exit']==0 and v['stdout'] in ['200','301','302'] for v in result['genericHTTP'].values())
result['udp443']={}
for family,ip in [(socket.AF_INET,'100.78.140.101'),(socket.AF_INET6,'fd7a:115c:a1e0::5901:8c9c')]:
 s=socket.socket(family,socket.SOCK_DGRAM);s.settimeout(3);start=time.monotonic()
 try:
  s.connect((ip,443));s.send(b'CWA transport diagnostic');s.recv(512);outcome='unexpected response'
 except ConnectionRefusedError:outcome='ICMP port unreachable'
 except Exception as e:outcome=type(e).__name__
 finally:s.close()
 result['udp443'][ip]={'outcome':outcome,'elapsedMs':round((time.monotonic()-start)*1000)}
result['checks']['directQUICFastFail']=all(x['outcome']=='ICMP port unreachable' for x in result['udp443'].values())
result['egress']=run(['curl','-sS','--max-time','12','https://www.cloudflare.com/cdn-cgi/trace'])
result['stopWeather']=run(['osascript','-e','tell application "Weather" to quit'])
result['stopWeatherDaemon']=run(['killall','-u','jamie','weatherd'])
result['stopWidget']=run(['killall','-u','jamie','WeatherWidget'])
time.sleep(1)
result['coldStartAt']=time.time();result['startWeather']=run(['open','-a','Weather'])
time.sleep(18)
result['weatherConnections']=run(['sh','-c','lsof -nP -iTCP -iUDP | grep -E "Weather|weatherd"'])
result['checks']['nativeTCPConnectedToPi']='100.78.140.101:443 (ESTABLISHED)' in result['weatherConnections']['stdout']
result['finishedAt']=time.time()
print(json.dumps(result,ensure_ascii=False,indent=2))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','jamie@100.122.163.78','python3','-'],input=script,capture_output=True,text=True,timeout=160)
(OUT/'mac-acceptance.stderr').write_text(p.stderr)
if p.returncode:
 (OUT/'mac-acceptance.json').write_text(json.dumps({'sshExit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}));raise SystemExit(p.returncode)
r=json.loads(p.stdout)
rows=[]
for line in (ROOT/'logs/bridge-reverse.jsonl').read_text().splitlines():
 try:
  d=json.loads(line)
  if d.get('time',0)>=r['coldStartAt'] and d.get('status')=='modified':rows.append(d)
 except ValueError:pass
r['nativeResponses']=rows;r['checks']['nativeResponseModified']=bool(rows)
r['checks']['nativeAppModified']=any('Weather_macOS' in x.get('app','') for x in rows)
r['checks']['nativeWidgetModified']=any('WeatherWidget_macOS' in x.get('app','') for x in rows)
r['relayApproval']=json.loads(subprocess.check_output([str(ROOT/'.venv/bin/python'),'split_routes.py','status'],cwd=ROOT,text=True))
r['dnsOnlyMacResult']='passed' if all(r['checks'].values()) else 'check-details'
(OUT/'mac-acceptance.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print(json.dumps({'result':r['dnsOnlyMacResult'],'checks':r['checks'],'responses':len(rows),'relayRoutesReady':r['relayApproval']['relayRoutingReady']},ensure_ascii=False))
