# 架構與程式導覽

## 實際封包

```http
GET /api/v2/weather/zh-Hant-TW/<latitude>/<longitude>?country=TW&timezone=Asia/Taipei&dataSets=...
Host: weatherkit.apple.com
Accept: application/vnd.apple.flatbuffer;messageType=WK2.Weather
```

這是已擷取原生天氣的私有 FlatBuffers 協定。公開 WeatherKit REST schema 僅可當研究線索。iOS、macOS 與 Widget 的 requested dataSets 與回應大小各異。

## 正式資料流與連接埠

```text
裝置 Core Location 或搜尋城市 -> Apple Weather 的 request 座標
  -> Tailscale restricted DNS -> AdGuard 裝置限定 weatherkit A=100.78.140.101
  -> Pi5 Tailscale Serve TCP/443 -> 127.0.0.1:19443 SNI router
       weatherkit.apple.com -> 127.0.0.1:18443 mitmproxy reverse
          -> Apple 原始 HTTPS response
          -> 100.78.140.101:18880 /v1/cwa/weather
          -> 127.0.0.1:18881 /transform
          -> 逐欄位改寫／必要 root 重建 -> 原生 App
       其他 SNI -> Pi5 Tailscale HTTPS :18444
          / -> 127.0.0.1:8017
          /runpod-image-editor -> 127.0.0.1:8789

:18940 為限制 weatherkit 的 explicit forward proxy，保留測試用途。
```

服務的實際位址以 `infra/live-systemd/`、`infra/snapshots/tailscale-serve.json` 核對。SNI router 保留其他 TLS 流量穿透。公開憑證 profile 與 diagnostics 暴露於 tailnet；本機 codec 綁 loopback。

## 模組

| 檔案 | 職責 |
|---|---|
| addon.py | 目標 URL／country／MIME 篩選，3.5s 預算、備份原始內容、呼叫資料 API／codec、回退通知、紀錄 |
| api.py | FastAPI；diagnostics、health、normalized CWA、憑證下載、背景 warmup |
| cwa_client.py | allowlisted CWA REST/File/Linked API，認證、4 並行下載、dataset lock、TTL／有界 stale／60s backoff |
| cwa_snapshot.py | 座標到觀測／鄉鎮／雨量／AQI／格點的整合，來源標記 |
| cwa_model.py | 數值驗證、单位、露點、觀測與預報標準化、地理距離 |
| cwa_products.py | 溫度分析與一小時 radar QPF；座標轉換 |
| cwa_nwp.py / model_worker.py | WRF 格點正規化／背景 HTTP Range + GRIB2 子集驗證與快取 |
| cwa_alerts.py / cwa_astronomy.py / cwa_aqi.py | 警報、天文、環境部 AQI LinkedAPI |
| mapper.mjs | FlatBuffers known scalar 寫入、時窗轉換、AQI／警報 root 重建 |
| flatbuffer_expand.mjs | 原始 buffer 中省略 scalar 的追加／table 擴充，保留未知 payload |
| weather_math.mjs | 完整時窗雨量分配、模式氣壓內插 |
| codec_server.mjs | Node HTTP codec server |
| vendor/weatherkit-codec.full.mjs | NSRingo WeatherKit v3.3.2 bundle 衍生 codec；保留 Apache NOTICE |
| sni_router.py | ClientHello/SNI 解析與雙向 TLS passthrough |
| bridgectl.py | 裝置 opt-in DNS 規則、備份／失敗復原、reload routing |
| split_routes.py / network_rules.py | 子網路宣告、核准狀態、DNS快照、nft QUIC/IPv6 fallback |

## 重要限制

原始 Apple response 先取得，才開始 CWA＋codec 3.5s 計時。代理本身離線、Apple上游連線失敗、TLS錯誤屬另外的故障路徑。
As of 2026-09-20, active CWA disk/memory entries refresh within 60 seconds of expiry on a 30-second warmup loop. Valid cache hits do not wait on an ongoing refresh lock. Original TTL and stale limits remain unchanged; full Apple responses are not cached. See [PERFORMANCE](PERFORMANCE.md) for measurements and limitations.
未知欄位維持 Apple，合法零值與省略欄位是兩種情況；省略 scalar 的擴充已有回歸測試。
變更 root 後應重新解碼驗證。報告中的 offset 可能屬擴充前階段，請以最終 getter 值與來源做核對。
