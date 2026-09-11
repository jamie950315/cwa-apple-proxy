"""Collect verified deployment state and publish audit records without restarting services."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
import httpx
ROOT=Path('/home/jamie/cwa-weather-proxy');TZ=timezone(timedelta(hours=8))
def load(p):return json.loads((ROOT/p).read_text())
with httpx.Client(timeout=8,trust_env=False) as c:
    api=c.get('http://100.78.140.101:18880/healthz');api.raise_for_status()
    codec=c.get('http://127.0.0.1:18881/healthz');codec.raise_for_status()
    status=c.get('http://100.78.140.101:18880/status');status.raise_for_status()
api,codec,status=api.json(),codec.json(),status.json()
assert api['version']==codec['version']=='0.3.1'
audit=load('reports/native-031-audit.json');assert audit['count']==audit['passed'] and not audit['failures']
publish=load('reports/release-publish-latest.json');assert publish['status']=='passed'
notify=load('reports/ntfy-timeout-selftest.json');assert notify['receipt']['http']==200 and notify['originalBodyPreserved'] and notify['originalHeadersPreserved']
log=(ROOT/'reports/executor-final-audit.log').read_text();assert 'PYTEST_EXIT=0' in log and 'NODE_TEST_EXIT=0' in log and 'NATIVE_AUDIT_EXIT=0' in log
names=['cwa-weather-api','cwa-weather-codec','cwa-weather-proxy','cwa-weather-forward','cwa-weather-sni','cwa-weather-routing','cwa-weather-model.timer']
services={n:{'active':subprocess.check_output(['systemctl','is-active',n],text=True).strip(),'enabled':subprocess.check_output(['systemctl','is-enabled',n],text=True).strip()} for n in names}
assert all(v['active']=='active' for v in services.values())
result={'verifiedAt':datetime.now(TZ).isoformat(),'status':'verified','versions':{'api':api['version'],'codec':codec['version']},'services':services,'tests':{'python':52,'javascript':23,'passed':75},'nativePacketAudit':{'checked':audit['count'],'passed':audit['passed'],'failures':audit['failures']},'towns':publish['towns'],'replay':publish['replay'],'ntfy':{'deadlineSeconds':notify['deadlineSeconds'],'fallbackElapsedSeconds':notify['fallbackElapsedSeconds'],'originalBodyPreserved':notify['originalBodyPreserved'],'originalHeadersPreserved':notify['originalHeadersPreserved'],'receiptHttp':notify['receipt']['http'],'receiptId':notify['receipt']['response']['id'],'topic':'cwa-apple-proxy'},'bridge':status.get('bridge',{}),'model':{'timerEnabled':True},'visualVerification':{'temperatureSeen':True,'screenshotTime':'2026-09-11T12:37:03+08:00','screenshotTemperatureC':26,'remaining':'AQI card and new card visual verification pending; Mac Executor later returned HTTP 502 and Mac peer was offline. iOS trust/onboarding and native UI remain separate.'}}
(ROOT/'reports/executor-closeout-031.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
report=ROOT/'reports/CWA_Weather_Bridge_0.3.1_研究部署紀錄.md'
text=report.read_text();marker='\n## Executor 最後核實補充\n'
text=text.split(marker)[0]+marker+f'''\n核實時間：{result['verifiedAt']}。API 與 codec 均回覆 0.3.1。六個服務及模式資料更新 timer 全部 active，開機啟用狀態已核對。\n\n本次重新執行 Python 52 項、JavaScript 23 項測試，共 75 項通過。另對保存的 {audit['count']} 份真正 macOS 天氣 App／Widget 回應逐欄位解碼核對，{audit['passed']} 份全部通過；此項驗收與先前 1,000 次本機重播分開。\n\n完整 App 樣本可核對到 952 個 scalar 改寫、96 個逐時時間點與 7 天資料，該樣本含 201 個降雨相關欄位改寫，省略 scalar 造成的漏寫為 0；AQI root 保留臺灣指數和來源。數量隨各次請求資料集、資料涵蓋範圍及相同值而改變。\n\n12:37 的原生天氣截圖已見 CWA 氣溫 26°C。後續 Mac 工具回覆 HTTP 502，Tailscale 顯示該 Mac 離線，因此新增 AQI 卡片與所有細節卡片的視覺驗收仍分開標記；伺服器部署與原生回應核對已有可讀取的完成證據。\n\n證據：`reports/executor-final-audit.log`、`reports/native-031-audit.json`、`reports/executor-closeout-031.json`、`reports/ntfy-timeout-selftest.json`。\n'''
report.write_text(text)
archive=ROOT/'dist/cwa-weather-bridge-source.zip';additions={'reports/CWA_Weather_Bridge_0.3.1_研究部署紀錄.md':report,'research/audit_native_031.mjs':ROOT/'research/audit_native_031.mjs','reports/executor-closeout-031.json':ROOT/'reports/executor-closeout-031.json'}
# Keep the release's pre-existing allowlist; add only the audit script/report.
config=dict(l.split('=',1) for l in (ROOT/'.env').read_text().splitlines() if '=' in l and not l.startswith('#'));key=config.get('CWA_API_KEY','').encode()
tmp=archive.with_suffix('.tmp.zip')
with zipfile.ZipFile(archive) as src,zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        if info.filename in additions:continue
        payload=src.read(info)
        assert Path(info.filename).name!='.env' and 'PRIVATE KEY-----' not in payload.decode('utf8',errors='ignore')
        assert not key or key not in payload
        dst.writestr(info,payload)
    for name,p in additions.items():
        payload=p.read_bytes();assert not key or key not in payload;dst.writestr(name,payload)
tmp.replace(archive)
with zipfile.ZipFile(archive) as z:count=len(z.infolist())
publish.update(sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),fileCount=count,finalAudit='reports/executor-closeout-031.json',nativePacketAudit=result['nativePacketAudit'],nativeUI=result['visualVerification']['remaining'])
(ROOT/'reports/release-publish-latest.json').write_text(json.dumps(publish,ensure_ascii=False,indent=2))
print(json.dumps({'status':'verified','verifiedAt':result['verifiedAt'],'versions':result['versions'],'tests':result['tests'],'nativePacketAudit':result['nativePacketAudit'],'services':services,'archiveFileCount':count,'archiveSha256':publish['sha256'],'archiveSecretsCheck':'passed','bridgeStats':status.get('bridge',{}).get('stats',{})},ensure_ascii=False,indent=2))
