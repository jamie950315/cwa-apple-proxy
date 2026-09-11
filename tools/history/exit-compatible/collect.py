from pathlib import Path
from datetime import datetime
import json,subprocess,shutil,time
ROOT=Path('/home/jamie/cwa-weather-proxy');OUT=ROOT/'research/exit-compatible';DEST=ROOT/'reports/exit-compatible-native';DEST.mkdir(parents=True,exist_ok=True)
MAC='/Users/jamie/cwa-weather-research/exit-compatible'
for name in ['matrix.json','A1-JP.fresh.json','A1-US.fresh.json','Pi5.fresh.json','jp-tyo-wg-001.fresh.json']:
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=8','jamie@100.122.163.78:'+MAC+'/'+name,str(OUT/('mac-'+name))],check=True,timeout=30)
m=json.loads((OUT/'mac-matrix.json').read_text())
assert m['restored'] is True,'Matrix failed to restore original exit'
fresh={}
for name in ['A1-JP','A1-US','Pi5','jp-tyo-wg-001']:
    d=json.loads((OUT/('mac-'+name+'.fresh.json')).read_text());assert d.get('restored') is True,name+' test still running or un-restored';fresh[name]=d
log=[]
for line in (ROOT/'logs/bridge-reverse.jsonl').read_text().splitlines():
    try:log.append(json.loads(line))
    except ValueError:pass
results=[];proofs={}
for r in m['results']:
    name=r['name'];windows=[]
    if r.get('coldStartAt'):windows.append((r['coldStartAt'],r['finishedAt']))
    if name in fresh:windows.append((fresh[name]['uiReadyAt'],fresh[name]['finishedAt']))
    rows=[e for e in log if e.get('status')=='modified' and 'Weather_macOS' in e.get('app','') and any(int(a)<=e.get('time',0)<=int(b) for a,b in windows)]
    seen=set();rows=[e for e in rows if e.get('proof') and not(e['proof'] in seen or seen.add(e['proof']))]
    for e in rows:
        p=(ROOT/e['proof']).resolve()
        if not p.is_relative_to((ROOT/'data/proofs').resolve()):raise ValueError('Unsafe proof path')
        dest=DEST/p.name
        if p.exists() and not dest.exists():shutil.copytree(p,dest)
        if dest.exists():proofs[str(dest)]={'exit':name,'event':e}
    checks=r['checks']
    network=all(checks.get(k) is True for k in ['exitSelection','nativeWeatherDNS','quadWeatherDNS','relayDNS','relaySpecificRoute','nativeTCPToPi','exitStayedSelected'])
    full=network and checks.get('ordinaryInternet') is True and checks.get('httpHealthy') is True and bool(rows)
    item={'exit':name,'networkAndDNSVerified':network,'ordinaryInternet':checks.get('ordinaryInternet'), 'normalHTTPHealthy':checks.get('httpHealthy'), 'egressCountry':r.get('egress',{}).get('loc'),'nativeResponseCount':len(rows),'nativeFields':[e['fields'] for e in rows],'nativeTranslationMs':[e['elapsedMs'] for e in rows],'status':'passed' if full else 'internet-unavailable' if not checks.get('ordinaryInternet') else 'review','initialChecks':checks,'evidenceWindows':windows}
    if name in fresh:item['supplementary']={k:fresh[name].get(k) for k in ['exitSelectionVerified','exitStayedSelected','restored','udp4Attempts','status']}
    results.append(item)
(OUT/'native-proof-list.json').write_text(json.dumps(list(proofs),indent=2))
(OUT/'native-proof-index.json').write_text(json.dumps(proofs,ensure_ascii=False,indent=2))
summary={'verifiedAt':datetime.now().astimezone().isoformat(),'transportVersion':'1.0.2','dataVersion':'0.3.1','configurationChange':'Use with exit node enabled for all four restricted Pi5 DNS entries; existing globals and subnet routes unchanged','macOriginalRestored':True,'testedPlatform':'macOS 27.0','results':results,'preservedProofs':len(proofs),'limits':['Actual exit switching was tested on Mac; current iPhone exit choice is not remotely observable.','jarvis ordinary public egress/HTTP probes failed; no guarantee for an exit node with an unavailable internet path.','First cold-start matrix had no fresh response in some 40-second windows; supplementary new-city queries are kept as separate evidence.','Initial UDP probes timed out once on Pi5 and once on jp-tyo-wg-001; subsequent three spaced probes per node all received refusal. Core ICMP limits remain unchanged.']}
(OUT/'collected-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({'results':[{k:r[k] for k in ['exit','status','nativeResponseCount','egressCountry']} for r in results],'proofs':len(proofs)},ensure_ascii=False))
