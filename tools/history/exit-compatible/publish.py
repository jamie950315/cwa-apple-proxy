from pathlib import Path
from datetime import datetime
import json,re,subprocess,zipfile,hashlib,urllib.request,time
ROOT=Path('/home/jamie/cwa-weather-proxy');OUT=ROOT/'research/exit-compatible'
def command(args,timeout=30):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError(str(args[0])+' exit '+str(p.returncode)+': '+p.stderr[-1000:])
    return p.stdout

def api(path):
    op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with op.open('http://100.78.140.101:18880'+path,timeout=8) as r:return json.load(r)

py=command([str(ROOT/'.venv/bin/python'),'-m','pytest','tests','-q']);(OUT/'tests-python-final.log').write_text(py)
js=command(['node','--test',*[str(p) for p in (ROOT/'tests').glob('*.test.mjs')]]);(OUT/'tests-node-final.log').write_text(js)
command(['node','--check',str(OUT/'dashboard-script.js')])
pycount=int(re.search(r'(\d+) passed',py).group(1));jscount=int(re.search(r'pass (\d+)',js).group(1))
s=json.loads((OUT/'collected-summary.json').read_text());audit=json.loads((OUT/'native-audit.json').read_text());assert audit['count']==audit['passed'] and audit['count']>0
command(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=8','jamie@100.122.163.78:/Users/jamie/cwa-weather-research/exit-compatible/final-restore.json',str(OUT/'mac-final-restore.json')])
restore=json.loads((OUT/'mac-final-restore.json').read_text());assert restore['originalRestored']
services={n:{'active':command(['systemctl','is-active',n]).strip(),'enabled':command(['systemctl','is-enabled',n]).strip()} for n in ['AdGuardHome','cwa-weather-api','cwa-weather-codec','cwa-weather-proxy','cwa-weather-forward','cwa-weather-sni','cwa-weather-routing','cwa-weather-route-status.timer','cwa-weather-model.timer']}
verified=datetime.now().astimezone().isoformat()
public={**{k:s[k] for k in ['transportVersion','dataVersion','testedPlatform','macOriginalRestored']},'verifiedAt':verified,'status':'configured-and-verified-for-tested-operational-exits','results':[{k:r[k] for k in ['exit','networkAndDNSVerified','ordinaryInternet','normalHTTPHealthy','egressCountry','nativeResponseCount','nativeFields','nativeTranslationMs','status']} for r in s['results']],'nativeAudit':{'packets':audit['count'],'passed':audit['passed'],'scalarComparisons':audit['checkedFields']},'tests':{'python':pycount,'javascript':jscount,'total':pycount+jscount},'limits':s['limits']}
path=ROOT/'data/exit-compatibility-status.json';temp=path.with_suffix('.tmp');temp.write_text(json.dumps(public,ensure_ascii=False,indent=2));temp.replace(path)
command(['sudo','-n','systemctl','start','cwa-weather-route-status.service'])
status=api('/status');assert status['splitRoutes']['configurationReady'] and status['splitRoutes']['exitNodeSelection']=='optional'
assert status['exitCompatibility']['nativeAudit']['passed']==audit['passed']
assert status['splitRoutes']['exitCompatibleDNS']['allFourEnabledAtVerification'] is True
rows=[]
for r in public['results']:
    result='通過' if r['status']=='passed' else '一般網際網路探測逾時；完整驗收保留'
    rows.append('| '+r['exit']+' | '+(r['egressCountry'] or '未取得')+' | '+('Pi5' if r['networkAndDNSVerified'] else '待核對')+' | '+str(r['nativeResponseCount'])+' | '+result+' |')
report=f'''# CWA Weather Bridge Exit Node 共存設定與驗收

核實時間：{verified}。傳輸／DNS 設定 1.0.2；資料翻譯層 0.3.1。

## 完成項目

Tailscale 管理頁中，下列四個 Restricted DNS 皆保持 nameserver `100.78.140.101`，並逐項開啟、儲存「Use with exit node／搭配出口節點使用」：

- `weatherkit.apple.com`
- `tthr.apple.com`
- `tether.edge.apple`
- `tether.v.aaplimg.com`

既有全域 nameserver、其他 DNS 分流、Pi5 LAN／relay 子網路廣告、CA 與 CWA 資料翻譯程式保持原功能。1.0.2 更新診斷為「Exit Node 可選」，並保存最後一次開關確認及逐節點測試資料。防火牆 render_rules 函式與 1.0.1 備份逐字比較一致。

## 實際出口切換

測試平台為 Mac，選擇節點前後均讀取 Tailscale prefs 核對 ID；Quad100 與 macOS 原生 DNS 都確認 weatherkit 指向 Pi5。一般上網另外讀取 public egress，天氣回應使用原生 App 新請求與 Pi5 封包證據核對。

| Exit Node | 上網出口國別 | 天氣 DNS／Pi5 連線 | 新原生回應數 | 結果 |
|---|---|---|---:|---|
{chr(10).join(rows)}

「無」與五個正常可上網的出口均有完整成功證據。兩個 Mullvad 節點是本輪抽樣的日本／美國出口；其他節點的可用性仍受其連線、存取權及 Tailscale DNS／子網路路由設定影響。

jarvis 已可選為出口，天氣 DNS、Pi5 TCP 與 relay 分流探測成立，但一般公網探測逾時，Apple／Google 公網 HTTP 測試失敗。本輪將其記為出口網路不可用，原因未進一步診斷；其 CWA 新原生請求驗收保留。

## 封包與回歸測試

- 真正原生 Weather 回應保留 {audit['count']} 份，逐欄位重新解碼 {audit['checkedFields']} 次比較全部通過。
- Python {pycount} 項、JavaScript {jscount} 項，共 {pycount+jscount} 項測試通過。
- Mac 已還原原設定：ExitNodeID、ExitNodeIP 皆為空；CorpDNS、RouteAll、ExitNodeAllowLANAccess 與測試前相同，一般路由回到 en0。
- 相關服務與計時器核實皆 active／enabled。

初輪對同一城市冷啟動的部分 40 秒觀察窗未取得新的天氣回應；後續切換 A1-JP 搜尋屏東、A1-US 搜尋南投、Pi5 搜尋臺東、Mullvad 日本搜尋彰化，均捕獲新的 CWA 改寫。原始觀察窗與補測分開保存，並未將早期缺少新封包的結果改写為成功。

初輪 Pi5 與 Mullvad 日本各有一個 UDP 拒絕探測逾時；補測分別執行三次間隔探測，全部收到快速拒絕。核心 ICMP 限制保持原樣；測試結果表示後續重試通過，並不保證網路零丟包。

## 實際路徑與使用條件

```text
一般上網 → 所選 Exit Node；選「無」時 → 原網路出口
天氣 DNS → Pi5 AdGuard
天氣 API／指定 relay 網段 → Pi5 → CWA 翻譯服務
```

裝置需保持 Tailscale DNS、接受子網路路由、CA 完整信任及中轉裝置名單。分流以目的 IP 為單位，共用指定 relay IP 的其他 Apple 流量也可能經 Pi5。

iPhone 與 Mac 套用同一份 tailnet DNS 政策，iPhone 先前已驗證原生天氣與小工具中轉成功；本輪逐個出口的切換測試使用 Mac，未遠端更動 iPhone 出口選擇。iPhone 每一節點／不同網路的真機驗收仍需獨立執行。

原有 3.5 秒翻譯期限、Apple 原始資料回退與 ntfy `cwa-apple-proxy` 通知程式保持不變。該期限從已取得 Apple 回應後計算，出口或 Pi5 本身的網路失效另屬傳輸層故障。AQI 自訂量尺卡片 404 為既有獨立問題，這轮未修改。

## 操作及證據

診斷頁：`http://100.78.140.101:18880/`；`/status` 含 `exitCompatibility`、`splitRoutes`。

- `research/exit-compatible/mac-matrix.json`：初輪七種模式的原始探測。
- `research/exit-compatible/mac-*.fresh.json`：新城市补測與還原紀錄。
- `research/exit-compatible/mac-final-restore.json`：最後還原核對。
- `research/exit-compatible/native-audit.json`：原生封包逐欄位比較。
- `reports/exit-compatible-native/`：永久保留本輪原始／改寫封包。
- `config/exit-dns-compatibility.json`：DNS 開關最後一次管理頁確認；該檔提供時點證據，CLI 未持續監控管理頁開關。

官方機制參考：
- https://tailscale.com/docs/reference/dns-in-tailscale
- https://tailscale.com/docs/features/exit-nodes
- https://tailscale.com/docs/reference/route-injection
'''
report=report.replace('改写','改寫').replace('這轮','這輪').replace('补測','補測')
report_path=ROOT/'reports/CWA_Weather_Exit_Node_1.0.2_共存驗收.md';report_path.write_text(report)
archive=ROOT/'dist/cwa-weather-bridge-source.zip'
with zipfile.ZipFile(archive) as z:names=z.namelist()
names=sorted(set(names+['config/exit-dns-compatibility.json','tests/test_exit_compatibility.py']))
names=[n for n in names if not any(part in ['reports','research','data','certs','backups','.env'] for part in Path(n).parts)]
secret=dict(l.split('=',1) for l in (ROOT/'.env').read_text().splitlines() if l and not l.startswith('#') and '=' in l).get('CWA_API_KEY','').encode()
tmp=archive.with_suffix('.tmp');written=[]
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
    for name in names:
        p=(ROOT/name).resolve()
        assert p.is_relative_to(ROOT.resolve()) and p.is_file(),name
        assert not any(part in ['certs','.env','backups','research','reports','data'] for part in Path(name).parts),name
        raw=p.read_bytes();assert not(secret and secret in raw),name+' contains CWA key';assert b'-----BEGIN PRIVATE KEY-----' not in raw and b'-----BEGIN RSA PRIVATE KEY-----' not in raw,name
        z.writestr(name,raw);written.append(name)
tmp.replace(archive)
final={'verifiedAt':verified,'transportVersion':'1.0.2','configurationReady':True,'configuredUseWithExitNode':4,'macOriginalRestored':True,'tests':public['tests'],'nativeAudit':public['nativeAudit'],'results':public['results'],'services':services,'proxyStats':status.get('bridge',{}).get('stats'),'report':str(report_path),'archive':{'files':len(written),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'secretsCheck':'passed'}}
(ROOT/'reports/exit-compatibility-final.json').write_text(json.dumps(final,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in final.items() if k not in ['services','results']},ensure_ascii=False))
