# CWA Weather Bridge 免 Exit Node 核准後驗收

核實時間：2026-09-11T15:50:03.567306+08:00。傳輸層 1.0.1；資料翻譯層 0.3.1。

## 結果

四條 relay 子網路已核准並同步到受測 Mac；Mac Exit NodeID／IP 均為空，系統 HTTP／HTTPS／PAC 代理保持關閉，一般網際網路走 en0，Pi5 與指定 relay 目的地走 Tailscale。
本輪在 Tailscale 管理頁補上四條 restricted DNS，已由 Mac 與 Pi5 的 DNS 設定核對；全域 nameserver 與原有 ts.net DNS 分流保留。

| 驗收 | 結果 |
|---|---|
| Python / JavaScript 回歸 | 72 + 23 = 95 項通過 |
| Mac 實際傳輸檢查 | 13 項全部通過 |
| 最後冷啟動後原生回應 | Weather 2 筆，Widget 0 筆 |
| 重新解碼核對原生回應 | 2/2 通過 |
| 一般網站／既有 Pi5 服務 | Apple、Google、Pi5 首頁、Runpod 路徑與 CWA health 均 HTTP 200 |
| 普通網際網路出口 | 原本 Wi-Fi en0；Exit Node 保持 None |
| 四條 relay 子網路 | approved 4；pending 0 |
| 四個 restricted DNS | 全部指向 100.78.140.101 |
| IPv4 relay TCP | 實際 socket 連線成功 |
| IPv6 relay TCP | Pi5 缺少公網 IPv6 路由時快速 reset，促成 IPv4 回退 |

## 範圍與設定

Relay 目的網段：`17.253.0.0/16`、`2403:300:a00::/40`、`2620:149:a00::/40`、`2a01:b740:a00::/40`。
Restricted DNS：`weatherkit.apple.com`、`tthr.apple.com`、`tether.edge.apple`、`tether.v.aaplimg.com` → `100.78.140.101`。
Pi5 原有 Exit Node 宣告與 192.168.31.0/24 子網路保留；中轉裝置的 Exit Node 保持 None。路由依目的 IP 生效，共用這些目的 IP 的其他 Apple 連線，以及接受路由的其他 tailnet 裝置，也可能透過 Pi5。拒絕規則僅適用已加入中轉名單的裝置。

## 修正與測試界線

Pi5 缺少對外 IPv6 路由，使早期 IPv6 UDP 在進入 forward 前就得到 no-route，IPv6 TCP 曾等待 4 秒逾時。新規則在 prerouting 先處理已加入名單的 relay UDP；僅當目的 IPv6 FIB 路由缺失時，才對該 relay 的 TCP/443 回覆 reset。IPv4 TCP 與其他目的地保持通行。日後 Pi5 有對應 IPv6 路由時，TCP 條件自然停止匹配。
修正後最後一輪六個 UDP 目的地的拒絕延遲：{'17.253.87.61': 97, '2403:300:a04:2000::61': 96, '2620:149:af6::10': 101, '2a01:b740:a10:3000::21': 99, '100.78.140.101': 97, 'fd7a:115c:a1e0::5901:8c9c': 101} 毫秒；IPv6 TCP 回退 105 毫秒。
連續快速探測的一輪曾出現一個 IPv6 UDP 回覆逾時；原始紀錄保留為 mac-verification-burst.json。按 1.1 秒間隔重新測試後，六個目的地均正常快速拒絕。這項現象可能涉及 ICMP 限速／瞬時丟包，原因未經封包層完全確認；未停用核心限速，也未宣稱零丟包。
早期以猜測 Host 強制查詢 relay IP 的 HTTPS 探測得到憑證名稱不匹配；該筆保留為失敗。對此範圍的 TCP 通行驗證改為明確的 socket 連線；五個正常 HTTPS／HTTP 端點與原生 Weather 的中轉 TLS 另行驗證成功。

iPhone 仍為 pending：完整信任 CA、加入裝置導流名單以及 iOS 真機驗收須獨立完成。這輪保持 iPhone 的啟用狀態原樣。其他 Wi-Fi、行動網路與漫遊環境也屬獨立驗證範圍。既有 TAIWAN_AQI 卡片量尺 404 問題保留獨立處理。

## 維護

診斷頁：`http://100.78.140.101:18880/`。路由與 DNS 狀態每分鐘更新。既有 3.5 秒翻譯回退及 ntfy cwa-apple-proxy 通知維持原版程式。
本輪原始碼封存已更新，API key、.env 與私鑰掃描通過。
ZIP SHA-256：`7a802d8e64f76726724b45c3aaeb6fc5819f8362b4dc4108d793ff1ab0478159`。

主要證據：`reports/approved-split-final.json`、`research/approved-split/mac-verified-final.json`、`research/approved-split/native-audit.json`、`research/approved-split/config-final.json`。原始回應保存在 `reports/approved-split-native/`。

官方機制參考：
- https://tailscale.com/docs/reference/route-injection
- https://tailscale.com/docs/reference/dns-in-tailscale
- https://www.netfilter.org/projects/nftables/manpage.html
