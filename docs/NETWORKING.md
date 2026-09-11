# 網路、DNS 與 Exit Node 共存

## 已部署配置

Pi5 `100.78.140.101` / `fd7a:115c:a1e0::5901:8c9c`；Mac `100.122.163.78`；iPhone `100.123.14.68`。
Tailscale DNS四個restricted suffix：`weatherkit.apple.com`、`tthr.apple.com`、`tether.edge.apple`、`tether.v.aaplimg.com` -> Pi5。四條 **Use with exit node 已開啟**。
原有全域nameserver Pi5、A1-JP `100.91.87.20`、A1-US `100.116.187.43` 與 `ts.net` 分流保留。

Pi5特定廣告已核准：
```
17.253.0.0/16
2403:300:a00::/40
2620:149:a00::/40
2a01:b740:a00::/40
```

既有LAN `192.168.31.0/24` 與Exit Node `0.0.0.0/0`,`::/0` 廣告維持。一般流量走裝置選擇的出口或原網路，特定relay子網路與Pi5 tailnet連線繼續分流。
路由依目的IP，共用Apple位址的其他服務也可能經Pi5；其他接受該子網路的tailnet裝置也可能經Pi5。QUIC拒絕僅限定已加入CWA名單的client IP，TLS僅中轉weatherkit。

## 裝置 opt-in 與 DNS

`bridgectl.py` 備份AdGuard YAML，管理自己標記的規則，維持其他規則原樣。雙棧client selector以Peer list取得。
- weatherkit A -> Pi5，AAAA/HTTPS query給空回覆，避免h3/公網位址捷徑。
- 三個relay域名對已啟用裝置阻擋；舊cached／硬編碼relay IP以specific route+nft處理。
- macOS的PAC／explicit HTTP/HTTPS proxy保持關閉；`:18940`僅保留測試。
- 安裝CA與完整信任是分開步驟；既有iPhone與Mac均有真實HTTPS請求證據。

## QUIC與IPv6

Pi5 `inet cwa_weather` 拒絕已啟用裝置到Pi5或selected relay的UDP443，讓TCP嘗試能勝出。IPv6 relay UDP於prerouting提早處理，避免缺公網IPv6路由前置失敗拖延。
IPv6 TCP443僅在 `fib daddr oif missing` 時快速reset，讓IPv4可繼續；其餘TCP維持。Pi5取得可用目的IPv6路由時此條件自然不匹配。
曾有burst單次UDP回覆逾時，間隔重測通過；可能ICMP限速或瞬時丟包，原始原因仍未封包定論，保持核心限速。

## 判讀狀態

`split_routes.py status` 分開表示宣告、精確核准、DNS快照、IPv6可用性。預設 /0核准不代表specific route已核准。
Use with exit node的四個旗標由管理頁保存快照 `config/exit-dns-compatibility.json` 記錄，程式明示 `liveFlagMonitoring=false`，不把歷史快照包裝成即時輪詢。
`RouteAll=true` 表示接受子網路路由；客戶端選擇Exit Node以ExitNodeID/ExitNodeIP確認。

## 驗證原則

選出口後核對系統resolver、100.100.100.100解析、實际公開出口、Pi5路由與原生新城市請求。單純重啟App可使用快取，40s無新回應不直接判失敗；搜尋新的CWA城市並對時保存server proof。
切換測試先備份Mac偏好，用finally復原。jarvis跳過。iPhone各出口模式與不同Wi-Fi/行動網路仍按實際裝置獨立验收。

官方機制： https://tailscale.com/docs/reference/dns-in-tailscale 、https://tailscale.com/docs/reference/route-injection 、https://www.netfilter.org/projects/nftables/manpage.html 。
