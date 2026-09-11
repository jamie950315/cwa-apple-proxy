from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,subprocess,zipfile,hashlib,shutil,re,time
R=Path('/home/jamie/cwa-weather-proxy');D=R/'research/approved-split'
def run(args,timeout=30):
 p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(str(args[:2])+': '+p.stderr[-300:])
 return p.stdout
def read(name):return json.loads((D/name).read_text())
mac=read('mac-verified-final.json');assert mac['result']=='passed',mac['checks']
config=json.loads(run([str(R/'.venv/bin/python'),'split_routes.py','status','--write-status']));assert config['configurationReady']
run([str(R/'.venv/bin/python'),'research/approved-split/collect_native.py'])
audit=read('native-audit.json');native=read('native-summary.json');assert audit['count']>=2 and audit['count']==audit['passed']
py=(D/'tests-python-final.log').read_text();js=(D/'tests-node-final.log').read_text()
pycount=int(re.search(r'(\d+) passed',py).group(1));jscount=int(re.search(r'pass (\d+)',js).group(1));assert re.search(r'fail 0',js)
services={}
for name in ['AdGuardHome','cwa-weather-api','cwa-weather-codec','cwa-weather-proxy','cwa-weather-forward','cwa-weather-sni','cwa-weather-routing','cwa-weather-route-status.timer','cwa-weather-model.timer']:
 services[name]={'active':run(['systemctl','is-active',name]).strip(),'enabled':run(['systemctl','is-enabled',name]).strip()}
health=json.loads(run(['curl','-fsS','--max-time','8','http://100.78.140.101:18880/status']))
summary={'verifiedAt':datetime.now(timezone(timedelta(hours=8))).isoformat(),'transportVersion':'1.0.1','dataVersion':health['version'],'result':'verified-on-tested-Mac-network','routeConfig':config,'tests':{'python':pycount,'javascript':jscount,'total':pycount+jscount},'macLiveChecks':mac['checks'],'nativeResponses':{'app':native['appResponses'],'widget':native['widgetResponses'],'audited':audit['passed'],'examples':audit['items'][-3:]},'udpProbeMs':{k:v['elapsedMs'] for k,v in mac['udp'].items()},'tcpIPv4Ms':{k:v['elapsedMs'] for k,v in mac['tcp'].items() if ':' not in k},'ipv6TcpFallbackMs':next(v['elapsedMs'] for k,v in mac['tcp'].items() if ':' in k),'services':services,'bridgeStats':health.get('bridge',{}).get('stats',{}),'enrollment':json.loads((R/'clients.json').read_text()),'limitations':['Pi5 has no public IPv6 egress: enrolled relay IPv6 TCP fast-resets only when FIB destination route is missing; IPv4 is used for working connections.','Public relay subnet routing is destination-IP based, so shared Apple IPs and other accepting tailnet clients can be affected.','iOS CA trust/enrollment and roaming/mobile-network validation remain separate.','Existing TAIWAN_AQI scale-endpoint/card issue remains outside this transport change.','Initial burst test recorded one IPv6 UDP diagnostic timeout; subsequent paced final probe passed all six destinations. No loss-free guarantee is claimed.'],'changes':['Confirmed four previously pending routes approved and injected on Mac.','Added four restricted DNS entries via Tailscale admin UI, preserving global resolvers and ts.net configuration.','Deployed guarded IPv6 early QUIC reject and missing-egress TCP reset; source-client and destination-subnet scoping preserved.','Route status, UI and README updated; translation and ntfy code unchanged.']}
# Update existing public source archive while retaining its deliberately included fixtures.
archive=R/'dist/cwa-weather-bridge-source.zip';backup=R/'backups'/'source-before-approved-split.zip'
shutil.copy2(archive,backup)
with zipfile.ZipFile(archive) as z:entries={name:z.read(name) for name in z.namelist() if not name.endswith('/')}
updated=0
for name in list(entries):
 p=(R/name).resolve()
 if p.is_relative_to(R) and p.is_file():entries[name]=p.read_bytes();updated+=1
# Exact expected deployment files must exist without an archive path prefix.
for name in ['network_rules.py','split_routes.py','dashboard.html','README.md','config/split-routing.json','tests/test_split_routes.py']:
 entries[name]=(R/name).read_bytes()
key=next((line.split('=',1)[1] for line in (R/'.env').read_text().splitlines() if line.startswith('CWA_API_KEY=')),None)
for name,data in entries.items():
 assert '.env' not in Path(name).parts and not name.startswith('certs/')
 assert not key or key.encode() not in data
 assert b'-----BEGIN PRIVATE KEY-----' not in data and b'-----BEGIN RSA PRIVATE KEY-----' not in data
new=archive.with_suffix('.tmp')
with zipfile.ZipFile(new,'w',zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(entries.items()):z.writestr(name,data)
new.replace(archive);summary['archive']={'files':len(entries),'updatedEntries':updated,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'secretScan':'passed'}
report=R/'reports/approved-split-final.json';report.write_text(json.dumps(summary,ensure_ascii=False,indent=2));(R/'data/transport-verification.json').write_text(json.dumps(summary,ensure_ascii=False))
lines=[
 '# CWA Weather Bridge 免 Exit Node 核准後驗收',
 '',f'核實時間：{summary["verifiedAt"]}。傳輸層 1.0.1；資料翻譯層 {summary["dataVersion"]}。',
 '', '## 結果', '',
 '四條 relay 子網路已核准並同步到受測 Mac；Mac Exit NodeID／IP 均為空，系統 HTTP／HTTPS／PAC 代理保持關閉，一般網際網路走 en0，Pi5 與指定 relay 目的地走 Tailscale。',
 '本輪在 Tailscale 管理頁補上四條 restricted DNS，已由 Mac 與 Pi5 的 DNS 設定核對；全域 nameserver 與原有 ts.net DNS 分流保留。',
 '', '| 驗收 | 結果 |','|---|---|',
 f'| Python / JavaScript 回歸 | {pycount} + {jscount} = {pycount+jscount} 項通過 |',
 f'| Mac 實際傳輸檢查 | {len(mac["checks"])} 項全部通過 |',
 f'| 最後冷啟動後原生回應 | Weather {native["appResponses"]} 筆，Widget {native["widgetResponses"]} 筆 |',
 f'| 重新解碼核對原生回應 | {audit["passed"]}/{audit["count"]} 通過 |',
 '| 一般網站／既有 Pi5 服務 | Apple、Google、Pi5 首頁、Runpod 路徑與 CWA health 均 HTTP 200 |',
 '| 普通網際網路出口 | 原本 Wi-Fi en0；Exit Node 保持 None |',
 '| 四條 relay 子網路 | approved 4；pending 0 |',
 '| 四個 restricted DNS | 全部指向 100.78.140.101 |',
 '| IPv4 relay TCP | 實際 socket 連線成功 |',
 '| IPv6 relay TCP | Pi5 缺少公網 IPv6 路由時快速 reset，促成 IPv4 回退 |',
 '', '## 範圍與設定', '',
 'Relay 目的網段：`17.253.0.0/16`、`2403:300:a00::/40`、`2620:149:a00::/40`、`2a01:b740:a00::/40`。',
 'Restricted DNS：`weatherkit.apple.com`、`tthr.apple.com`、`tether.edge.apple`、`tether.v.aaplimg.com` → `100.78.140.101`。',
 'Pi5 原有 Exit Node 宣告與 192.168.31.0/24 子網路保留；中轉裝置的 Exit Node 保持 None。路由依目的 IP 生效，共用這些目的 IP 的其他 Apple 連線，以及接受路由的其他 tailnet 裝置，也可能透過 Pi5。拒絕規則僅適用已加入中轉名單的裝置。',
 '', '## 修正與測試界線', '',
 'Pi5 缺少對外 IPv6 路由，使早期 IPv6 UDP 在進入 forward 前就得到 no-route，IPv6 TCP 曾等待 4 秒逾時。新規則在 prerouting 先處理已加入名單的 relay UDP；僅當目的 IPv6 FIB 路由缺失時，才對該 relay 的 TCP/443 回覆 reset。IPv4 TCP 與其他目的地保持通行。日後 Pi5 有對應 IPv6 路由時，TCP 條件自然停止匹配。',
 f'修正後最後一輪六個 UDP 目的地的拒絕延遲：{summary["udpProbeMs"]} 毫秒；IPv6 TCP 回退 {summary["ipv6TcpFallbackMs"]} 毫秒。',
 '連續快速探測的一輪曾出現一個 IPv6 UDP 回覆逾時；原始紀錄保留為 mac-verification-burst.json。按 1.1 秒間隔重新測試後，六個目的地均正常快速拒絕。這項現象可能涉及 ICMP 限速／瞬時丟包，原因未經封包層完全確認；未停用核心限速，也未宣稱零丟包。',
 '早期以猜測 Host 強制查詢 relay IP 的 HTTPS 探測得到憑證名稱不匹配；該筆保留為失敗。對此範圍的 TCP 通行驗證改為明確的 socket 連線；五個正常 HTTPS／HTTP 端點與原生 Weather 的中轉 TLS 另行驗證成功。',
 '', 'iPhone 仍為 pending：完整信任 CA、加入裝置導流名單以及 iOS 真機驗收須獨立完成。這輪保持 iPhone 的啟用狀態原樣。其他 Wi-Fi、行動網路與漫遊環境也屬獨立驗證範圍。既有 TAIWAN_AQI 卡片量尺 404 問題保留獨立處理。',
 '', '## 維護', '',
 '診斷頁：`http://100.78.140.101:18880/`。路由與 DNS 狀態每分鐘更新。既有 3.5 秒翻譯回退及 ntfy cwa-apple-proxy 通知維持原版程式。',
 '本輪原始碼封存已更新，API key、.env 與私鑰掃描通過。',
 f'ZIP SHA-256：`{summary["archive"]["sha256"]}`。',
 '', '主要證據：`reports/approved-split-final.json`、`research/approved-split/mac-verified-final.json`、`research/approved-split/native-audit.json`、`research/approved-split/config-final.json`。原始回應保存在 `reports/approved-split-native/`。',
 '', '官方機制參考：',
 '- https://tailscale.com/docs/reference/route-injection',
 '- https://tailscale.com/docs/reference/dns-in-tailscale',
 '- https://www.netfilter.org/projects/nftables/manpage.html',
]
md=R/'reports/CWA_Weather_No_Exit_Node_1.0.1_核准後驗收.md';md.write_text('\n'.join(lines)+'\n')
print(json.dumps({k:summary[k] for k in ['verifiedAt','result','tests','nativeResponses','udpProbeMs','archive']},ensure_ascii=False,indent=2))
