# 決策紀錄

| 決策 | 理由與保留條件 |
|---|---|
| 原生App作UI、Pi5作翻譯 | 符合使用者偏好，沿用現有Tailscale／AdGuard與自架主機 |
| 真實WK2 FlatBuffers擷取 | 原生App實際協定與公開WeatherKit JSON各有用途，實作以擷取結果為準 |
| CWA-first逐欄位混合 | 保留未整合欄位、時間缺口與Apple特殊資料，逐欄位provenance可查核 |
| scalar原位改寫＋省略scalar擴充 | 盡量維持未知payload；必要AQI/alert root重建後解碼驗證 |
| 3.5s硬預算＋原body/header回退 | 控制翻譯延遲，失敗保持已取得Apple內容；ntfy非同步避免通知拖住App |
| WRF背景Range子集 | 避免每個App请求下載約180MB模式檔；基於ETag、Content-Range與GRIB語意驗證 |
| 名稱限制CA、裝置opt-in | 將TLS攔截限定weatherkit，避免其他裝置未信任時被導流 |
| DNS+specific relay route+QUIC拒絕 | macOS會用relay/QUIC競速；只改DNS或PAC曾不足，補上特定網段分流 |
| Exit Node可選 | 1.0.2四restricted DNS的Use with exit node開啟，保持選定普通出口 |
| 兼容Pi5缺少公網IPv6 | 早期UDP拒絕，missing FIB的relay TCP reset促IPv4；其他TCP保留 |
| jarvis略過 | 使用者明示主機有問題，完整專案驗收不把它當待修blocker |
| 本機Git＋完整技術交接 | 使用者要求後續AI可接手；保留source hashes、文檔、實驗脚本、私有原始證據 |

## 已試過而非目前預設的路線

Mac PAC／全系統HTTPS proxy不能單獨涵蓋原生relay路徑；目前維持關閉。Pi5作全流量Exit Node曾用於最初驗證，後以specific route取代必要性。GitHub npm私有套件無法直接取得時，從NSRingo公開release bundle抽出codec並保留license/notice。
早期手動root CA信任／命令權限因不同Mac帳号context遇到阻礙，最終以實際HTTPS封包判斷。遠端管理拒絕權限時採已授權可用工具與SSH，不擴大host權限來規避。
