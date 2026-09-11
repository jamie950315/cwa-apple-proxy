# CWA Weather Bridge Exit Node 共存設定與驗收

核實時間：2026-09-11T17:21:37.649673+08:00。傳輸／DNS 設定 1.0.2；資料翻譯層 0.3.1。

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
| None | TW | Pi5 | 2 | 通過 |
| Pi5 | TW | Pi5 | 1 | 通過 |
| A1-JP | JP | Pi5 | 1 | 通過 |
| A1-US | US | Pi5 | 3 | 通過 |
| jarvis | 未取得 | Pi5 | 0 | 一般網際網路探測逾時；完整驗收保留 |
| jp-tyo-wg-001 | JP | Pi5 | 3 | 通過 |
| us-lax-wg-402 | US | Pi5 | 2 | 通過 |

「無」與五個正常可上網的出口均有完整成功證據。兩個 Mullvad 節點是本輪抽樣的日本／美國出口；其他節點的可用性仍受其連線、存取權及 Tailscale DNS／子網路路由設定影響。

jarvis 已可選為出口，天氣 DNS、Pi5 TCP 與 relay 分流探測成立，但一般公網探測逾時，Apple／Google 公網 HTTP 測試失敗。本輪將其記為出口網路不可用，原因未進一步診斷；其 CWA 新原生請求驗收保留。

## 封包與回歸測試

- 真正原生 Weather 回應保留 12 份，逐欄位重新解碼 10846 次比較全部通過。
- Python 76 項、JavaScript 23 項，共 99 項測試通過。
- Mac 已還原原設定：ExitNodeID、ExitNodeIP 皆為空；CorpDNS、RouteAll、ExitNodeAllowLANAccess 與測試前相同，一般路由回到 en0。
- 相關服務與計時器核實皆 active／enabled。

初輪對同一城市冷啟動的部分 40 秒觀察窗未取得新的天氣回應；後續切換 A1-JP 搜尋屏東、A1-US 搜尋南投、Pi5 搜尋臺東、Mullvad 日本搜尋彰化，均捕獲新的 CWA 改寫。原始觀察窗與補測分開保存，並未將早期缺少新封包的結果改寫為成功。

初輪 Pi5 與 Mullvad 日本各有一個 UDP 拒絕探測逾時；補測分別執行三次間隔探測，全部收到快速拒絕。核心 ICMP 限制保持原樣；測試結果表示後續重試通過，並不保證網路零丟包。

## 實際路徑與使用條件

```text
一般上網 → 所選 Exit Node；選「無」時 → 原網路出口
天氣 DNS → Pi5 AdGuard
天氣 API／指定 relay 網段 → Pi5 → CWA 翻譯服務
```

裝置需保持 Tailscale DNS、接受子網路路由、CA 完整信任及中轉裝置名單。分流以目的 IP 為單位，共用指定 relay IP 的其他 Apple 流量也可能經 Pi5。

iPhone 與 Mac 套用同一份 tailnet DNS 政策，iPhone 先前已驗證原生天氣與小工具中轉成功；本輪逐個出口的切換測試使用 Mac，未遠端更動 iPhone 出口選擇。iPhone 每一節點／不同網路的真機驗收仍需獨立執行。

原有 3.5 秒翻譯期限、Apple 原始資料回退與 ntfy `cwa-apple-proxy` 通知程式保持不變。該期限從已取得 Apple 回應後計算，出口或 Pi5 本身的網路失效另屬傳輸層故障。AQI 自訂量尺卡片 404 為既有獨立問題，這輪未修改。

## 操作及證據

診斷頁：`http://100.78.140.101:18880/`；`/status` 含 `exitCompatibility`、`splitRoutes`。

- `research/exit-compatible/mac-matrix.json`：初輪七種模式的原始探測。
- `research/exit-compatible/mac-*.fresh.json`：新城市補測與還原紀錄。
- `research/exit-compatible/mac-final-restore.json`：最後還原核對。
- `research/exit-compatible/native-audit.json`：原生封包逐欄位比較。
- `reports/exit-compatible-native/`：永久保留本輪原始／改寫封包。
- `config/exit-dns-compatibility.json`：DNS 開關最後一次管理頁確認；該檔提供時點證據，CLI 未持續監控管理頁開關。

官方機制參考：
- https://tailscale.com/docs/reference/dns-in-tailscale
- https://tailscale.com/docs/features/exit-nodes
- https://tailscale.com/docs/reference/route-injection
