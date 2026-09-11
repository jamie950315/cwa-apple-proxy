# 操作、部署與回復

## 唯讀核實

```sh
cd ~/cwa-apple-proxy
./scripts/pi-status.sh
ssh jamie@100.78.140.101 'cd /home/jamie/cwa-weather-proxy && .venv/bin/python bridgectl.py status && .venv/bin/python split_routes.py status'
```

`/healthz`回version/取數快取；`/status`含clients、最後改寫、codec、routes、exitCompatibility、通知；`/v1/cwa/weather?latitude=25.09&longitude=121.56`會實際取資料。
systemd model／route-status是oneshot，inactive/dead可代表該輪已結束，配合active timer判讀；proxy/api/codec/sni應active running，routing是active exited。

## 原始碼修改與部署

Mac repo為開發／交接；Pi5仍是正式環境，這次建立repo沒有部署新資料演算法。
1. 本機修改前讀HANDOFF與KNOWN_ISSUES，跑離線測試。將變更欄位、版本、假設、必要fixtures寫入報告。
2. 在Pi5唯讀核對目前檔案SHA與 `docs/evidence/production-source-manifest.json`。差異先人工整合，避免覆蓋其他工作。
3. 依使用者授權備份受影響檔案到Pi5 `backups/<timestamp>/`，記錄當時service狀態、units、Serve、clients與managed DNS；保留密鑰原位置及權限。
4. 只上傳核對過的變更檔案。Mac測試資料、`.private`、`clients.json`、CA及環境狀態應維持正式主機自己的內容。`rsync --delete`與全資料夾覆寫有刪除正式狀態風險。
5. 於Pi5以jamie身分跑pytest/node，通過後只restart受影響service。unit更新才daemon-reload；DNS／routing更新走bridgectl並保留其備份。
6. 查看新health、CWA快取、代理新回應；新城市觸發App，保存proof，再逐欄位解碼；UI新增卡片另截圖。
7. 故障時還原本次備份與對應service；網路回復優先 `bridgectl disable <IP>`，保留其他AdGuard設定。

本repo預設不附一鍵覆寫正式主機的命令，避免憑證／Tailscale Serve與既有服务被意外替換。`infra/live-systemd`為當時真實unit，`systemd`為來源檔，兩者差異已記錄。

## 新主機重建清單

現有source帶固定Pi5位址與部分絕對路徑，應先參數化或逐項替換並測試。固定字串搜尋：`100.78.140.101`、`/home/jamie/cwa-weather-proxy`、`/home/linuxbrew/.linuxbrew/bin/node`、`/opt/AdGuardHome/AdGuardHome.yaml`。
新主機建立專案根目錄／logs／data／certs／backups、jamie帳號或調整unit帳號。使用Python3.13與完整production鎖（含eccodes、numpy、pyproj），Node使用vendor codec，CWA key放`.env` 0600。
Tailscale、AdGuard為外部依賴；分開部署／驗證。保留新主機其他服务的Serve配置，依ARCHITECTURE建立TCP443至SNI、HTTPS18444與路徑轉送。enable核准specific routes、restricted DNS與Use with exit node。
CA產生／安裝是明確權限操作；歷史bootstrap脚本只供研究，現有CA不可重建覆寫。新CA上線需重新讓裝置完整信任，逐台opt-in。

## 常用維護

以下在**正式Pi5**操作：
```sh
cd /home/jamie/cwa-weather-proxy
systemctl status cwa-weather-api cwa-weather-codec cwa-weather-proxy cwa-weather-sni --no-pager
systemctl list-timers 'cwa-weather-*' --all --no-pager
journalctl -u cwa-weather-proxy -n 50 --no-pager
tail -n 5 logs/bridge-reverse.jsonl
# 移除單一裝置導流
sudo .venv/bin/python bridgectl.py disable <Tailscale-IP>
# 完整信任CA的新增裝置才可enable
sudo .venv/bin/python bridgectl.py enable <Tailscale-IP> --confirm-certificate-trusted
# 撤回本專案新增子網路；DNS導流另由bridgectl管理
sudo .venv/bin/python split_routes.py withdraw
```

`.private/runtime/clients.json`是交接快照，請以Pi5即時名單為準。iPhone在Tailscale顯示localhost，IPv4為100.123.14.68。

## 憑證／故障通知

```sh
# Pi5，只讀public cert資訊
openssl x509 -in certs/ca.pem -noout -subject -dates -fingerprint -sha256
openssl x509 -in certs/weatherkit.pem -noout -subject -dates
```

leaf約1年，CA約10年。續期優先沿用原CA簽發新leaf、原子替換、restart代理、驗證TLS；此專案目前手動維護，尚無自動續期服務。
3.5秒僅限已取得Apple response後的CWA/codec；Pi5整機離線需外部監測。ntfy測試會真實發送，標記TEST且避免重複騷擾。主題public可猜測，通知排除座標與金鑰。
