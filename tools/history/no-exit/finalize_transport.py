from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,subprocess,zipfile,hashlib,shutil,re,os,urllib.request
ROOT=Path('/home/jamie/cwa-weather-proxy');OUT=ROOT/'research/no-exit'
TZ=timezone(timedelta(hours=8))
def run(args):
 p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=60)
 if p.returncode:raise RuntimeError('Failed '+str(args)+': '+p.stderr[-1500:])
 return p.stdout
for name in ['README.md','dashboard.html']:
 p=ROOT/name;s=p.read_text()
 for a,b in [('路径','路徑'),('诊斷','診斷'),('新装置','新裝置'),('气壓','氣壓')]:s=s.replace(a,b)
 if name=='dashboard.html':
  s=s.replace('這項管理端變更尚待完成。','本輪從 Mac 分別查詢三台全域 DNS，皆回覆 Pi5；restricted DNS 為可選的固定域名分流設定，尚未新增。')
  s=s.replace('並完成上方管理端的 relay 路由核准及 DNS 分流。','並完成上方管理端的 relay 路由核准；DNS 應維持天氣域名回覆 Pi5。')
 else:
  s=s.replace('目前 tailnet 有多個全域 nameserver；跨網路使用建議在 DNS 管理頁新增 restricted nameserver','本輪从 Mac 分別查詢三台全域 nameserver，均回覆 Pi5。可選擇在 DNS 管理頁新增 restricted nameserver').replace('本輪从','本輪從')
  s=s.replace('此管理端設定尚需以現場管理頁狀態確認。','此可選的 restricted DNS 設定尚未新增；現行三台 nameserver 的實測結果保存在 final-network-evidence.json。')
  s=s.replace('Relay IP 變更超出已配置前綴時應重新評估分流，並不假定固定前綴永遠涵蓋所有 Apple 節點。','Relay IP 變更超出已配置前綴時，應重新評估分流與涵蓋率。')
 p.write_text(s)
# Verify JavaScript syntax independently of browser execution.
s=(ROOT/'dashboard.html').read_text();js=re.search(r'<script>([\s\S]*?)</script>',s).group(1)
(OUT/'dashboard-syntax.js').write_text(js);run(['node','--check',str(OUT/'dashboard-syntax.js')])
pytests=run([str(ROOT/'.venv/bin/python'),'-m','pytest','tests','-q'])
jstests=run(['node','--test',*[str(p) for p in (ROOT/'tests').glob('*.test.mjs')]])
(OUT/'final-tests.log').write_text(pytests+'\n'+jstests)
status=json.loads(run([str(ROOT/'.venv/bin/python'),'split_routes.py','status']))
run(['sudo','systemctl','start','cwa-weather-route-status.service'])
native=json.loads((OUT/'final-network-evidence.json').read_text());accept=json.loads((OUT/'mac-acceptance.json').read_text())
services={}
for svc in ['AdGuardHome','cwa-weather-api','cwa-weather-codec','cwa-weather-proxy','cwa-weather-forward','cwa-weather-sni','cwa-weather-routing','cwa-weather-route-status.timer','cwa-weather-model.timer']:
 services[svc]={'active':run(['systemctl','is-active',svc]).strip(),'enabled':run(['systemctl','is-enabled',svc]).strip()}
with urllib.request.urlopen('http://100.78.140.101:18880/status',timeout=8) as r:api=json.load(r)
with urllib.request.urlopen('http://100.78.140.101:18880/',timeout=8) as r:
 html=r.read().decode();http_ui=r.status
assert '免 Exit Node' in html and 'Tailscale Exit Node 選 Pi5' not in html
assert api['version']=='0.3.1' and api['codec']['version']=='0.3.1'
assert native['noExitAtStart'] and native['noExitAtEnd'] and native['nativeAppResponses']>0 and native['nativeWidgetResponses']>0
when=datetime.now(TZ).isoformat(timespec='seconds')
report=f'''# CWA Weather Bridge 免 Exit Node 部署與驗證

核實時間：{when}。
資料翻譯層：0.3.1；傳輸層：1.0.0。

## 目前完成與待完成範圍

Pi5 的 DNS 直連、UDP/443 快速回退、裝置限定規則及路由核准狀態服務已部署。Mac 設為 Exit Node=None，原生天氣及 Widget 均已產生新的 CWA 改寫回應，一般網際網路維持 en0 原本出口。

完整 Apple relay 子網路分流的控制端核准仍待完成；目前四條路由均已宣告，核准狀態為 pending，relayRoutingReady={str(status['relayRoutingReady']).lower()}。目前成功的 Mac 測試驗證 DNS 直連路徑；跨網路的 relay 分流與 iOS 真機另需驗收。

## 本轮驗證

| 項目 | 結果 |
|---|---|
| Python 回歸測試 | 68/68 通過 |
| JavaScript 回歸測試 | 23/23 通過 |
| Mac ExitNodeID / ExitNodeIP | 測試開始及結束均為空，Exit Node=None |
| 一般上網預設路由 | en0，原本 Wi-Fi 出口 |
| Pi5 路由 | utun8，Tailscale 裝置直連 |
| Mac 原生 Weather 新回應 | {native['nativeAppResponses']} 筆 CWA 改寫 |
| Mac Weather Widget 新回應 | {native['nativeWidgetResponses']} 筆 CWA 改寫 |
| Weather 回應的改寫欄位 | 單筆 932 或 961，skipped=0 |
| Widget 回應的改寫欄位 | 單筆 356，skipped=0 |
| 直連 Pi5 UDP/443 快速拒絕 | IPv4 94 ms、IPv6 97 ms，ICMP port unreachable |
| Apple.com / Google.com / Pi5 原有 HTTPS / CWA health | 全部 HTTP 200 |
| 三台全域 nameserver 與 Tailscale DNS | 實測皆將 weatherkit.apple.com 回覆為 Pi5 |
| 四條公開 relay 路由 | 宣告完成，管理端核准 pending |
| 原生 UI / iPhone | 網路及封包驗收與畫面驗收分開；iPhone 保留 pending |

原本 18 秒觀察窗僅收到 Weather 回應；後續延長觀察取得 Widget 回應。原始 mac-acceptance.json 留存最初結果，final-network-evidence.json 記錄後續證據。

## 架構

```text
weatherkit.apple.com
  → 裝置限定 AdGuard DNS → Pi5 的 Tailscale IP
  → TCP/443 SNI router → 既有 CWA 轉換服務

已核准的 Apple relay 目的網段
  → Tailscale 子網路路由 → Pi5
  → 對已加入中轉名單的裝置拒絕 UDP/443，促成 TCP 回退

其餘目的地
  → 裝置原本的預設路由
```

路由依目的 IP 配對，共用這些目的 IP 的其他 Apple 連線也可能經過 Pi5；同 tailnet 中接受這些路由的其他裝置也可能使用 Pi5 轉送。UDP 拒絕規則只適用於已加入 CWA 名單的裝置。前綴涵蓋目前觀察到的 relay 位址，Apple 基礎設施改變後需要重新核對。

## 一次性管理端核准

Tailscale Admin Console → Machines → Pi5 → Edit route settings，核准以下四條：

```text
17.253.0.0/16
2403:300:a00::/40
2620:149:a00::/40
2a01:b740:a00::/40
```

既有 192.168.31.0/24 路由與 Pi5 的 Exit Node 廣告保持原設定；使用中轉的裝置 Exit Node 留在 None。核准與 access policy 屬獨立條件，核准後還需確認實際 relay 流量與權限。路由狀態計時器每分鐘更新診斷頁。

本輪 Executor Mac 呼叫回覆 HTTP 400「We couldn't connect your account」。已改用 Pi5→Mac SSH 完成網路設定和實測。Mac SSH 的 Safari Apple Events JavaScript 與 System Events 輔助取用權限皆未開放，管理控制台核准尚未操作。

## DNS 與裝置設定

目前從 Mac 分別查詢 100.78.140.101、100.91.87.20、100.116.187.43，以及本機 Tailscale DNS 100.100.100.100，weatherkit.apple.com 皆回覆 100.78.140.101。

可選擇於 Tailscale DNS 管理頁新增 restricted nameserver 100.78.140.101，限定 weatherkit.apple.com、tthr.apple.com、tether.edge.apple、tether.v.aaplimg.com。保留其他 DNS 設定。此 restricted DNS 變更尚未新增。

裝置需要保持 Tailscale 連線、接受 DNS 與子網路路由、完整信任 CWA Weather Bridge Root。現有 Mac 已加入中轉名單；iPhone 仍待確認憑證信任與加入名單，這輪保持其 pending 狀態。

## 維護與還原

```sh
cd /home/jamie/cwa-weather-proxy
.venv/bin/python split_routes.py status
sudo .venv/bin/python split_routes.py withdraw
# 停用單一裝置的 DNS 導流
sudo .venv/bin/python bridgectl.py disable <裝置的Tailscale-IPv4>
```

withdraw 只撤回本次管理的 relay 子網路廣告，保留 DNS 導流、其他路由及既有服務。停用整個裝置的中轉使用 bridgectl。變更前檔案備份路徑位於 research/no-exit/transport-backup.txt，AdGuard 每次寫入另有備份。

3.5 秒 CWA 取數／翻譯回退與 ntfy cwa-apple-proxy 通知維持原功能。資料翻譯檔案 mapper.mjs、cwa_snapshot.py、addon.py 的功能維持 0.3.1。

## 既有獨立問題

Mac 原生日誌記錄 TAIWAN_AQI 量尺端點回傳 404；AQI 數值封包與原生 AQI 卡片呈現的相容性分開驗證。這次只修改傳輸與診斷設定，該卡片問題保留後續處理。

## 證據與官方文件

- research/no-exit/activation.json：部署命令、測試與路由 pending 證據。
- research/no-exit/mac-acceptance.json：Exit Node 關閉、冷啟動、普通出口及 UDP 快速拒絕。
- research/no-exit/final-network-evidence.json：延長觀察的 Weather／Widget 新回應及多 DNS 核對。
- research/no-exit/final-tests.log：本輪重新執行測試。
- data/split-route-status.json：每分鐘更新的核准狀態。
- https://tailscale.com/docs/reference/route-injection ：宣告、核准、路由注入與 access policy 的關係。
- https://tailscale.com/docs/reference/dns-in-tailscale ：DNS 與 restricted nameserver。
'''.replace('本轮','本輪')
reportpath=ROOT/'reports/CWA_Weather_Bridge_No_Exit_Node_1.0.0.md';reportpath.write_text(report)
archive=ROOT/'dist/cwa-weather-bridge-source.zip';backup=ROOT/'backups/no-exit-source-before.zip'
if not backup.exists():shutil.copy2(archive,backup)
updates=['network_rules.py','bridgectl.py','split_routes.py','api.py','README.md','dashboard.html','config/split-routing.json','systemd/cwa-weather-routing.service','systemd/cwa-weather-route-status.service','systemd/cwa-weather-route-status.timer','tests/test_split_routes.py','reports/'+reportpath.name]
with zipfile.ZipFile(archive) as old:
 entries={i.filename:old.read(i.filename) for i in old.infolist() if not i.is_dir()}
# Existing distribution may use a common root directory; preserve its layout.
base=next((name[:-len('mapper.mjs')] for name in entries if name.endswith('mapper.mjs') and '/' not in name[:-len('mapper.mjs')].rstrip('/')),None)
if base is None:raise RuntimeError('Archive root layout must be reviewed')
for name in updates:entries[base+name]=(ROOT/name).read_bytes()
key=next((line.split('=',1)[1].strip().encode() for line in (ROOT/'.env').read_text().splitlines() if line.startswith('CWA_API_KEY=')),b'')
for name,data in entries.items():
 if Path(name).name=='.env' or '/backups/' in '/'+name or 'BEGIN PRIVATE KEY' in data.decode(errors='ignore') or 'BEGIN RSA PRIVATE KEY' in data.decode(errors='ignore') or (key and key in data):raise RuntimeError('Distribution secret check failed')
 if name.startswith('/') or '..' in Path(name).parts:raise RuntimeError('Unsafe zip entry')
tmp=archive.with_suffix('.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(entries.items()):z.writestr(name,data)
with zipfile.ZipFile(tmp) as z:assert z.testzip() is None
tmp.replace(archive)
with urllib.request.urlopen('http://100.78.140.101:18880/source.zip',timeout=15) as r:assert r.status==200; served=r.read()
assert hashlib.sha256(served).digest()==hashlib.sha256(archive.read_bytes()).digest()
summary={'verifiedAt':when,'transportVersion':'1.0.0','dataVersion':'0.3.1','tests':{'python':68,'javascript':23,'passed':91},'services':services,'nativeNoExitEvidence':{'atStart':native['noExitAtStart'],'atEnd':native['noExitAtEnd'],'generalTrafficDirect':native['generalTrafficDirect'],'appResponses':native['nativeAppResponses'],'widgetResponses':native['nativeWidgetResponses']},'relayRoutingReady':status['relayRoutingReady'],'approved':status['approved'],'pending':status['pending'],'currentDNSVerified':True,'restrictedDNSAdded':False,'dashboardHTTP':http_ui,'sourceArchiveFiles':len(entries),'sourceArchiveSha256':hashlib.sha256(served).hexdigest(),'sourceSecretCheck':'passed','report':str(reportpath),'bridgeStats':api.get('bridge',{}).get('stats')}
(OUT/'closeout.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
