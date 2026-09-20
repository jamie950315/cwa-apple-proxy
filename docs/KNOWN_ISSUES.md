# 已知問題與待辦

## P1: Apple Watch Weather unavailable with iPhone Tailscale enabled

User A/B: disabling iPhone Tailscale restores Watch Weather. This confirms a path-dependent failure, not its exact cause. Watch trust of the custom WeatherKit CA is unverified; Apple requires installing a custom CA on both paired devices ([QA1948](https://developer.apple.com/library/archive/qa/qa1948/_index.html)). Current diagnostics can distinguish TLS failures from HTTP responses, but no Watch event has yet been identified. Controlled `unknown-ca` probes must not be attributed to Watch.

Keep existing iPhone/Mac enrollment and routing intact. Verify the Watch CA installation and reproduce with Tailscale enabled before changing relay DNS or QUIC policy. Installing a certificate on iPhone alone is not Watch acceptance. The archived Apple installation UI may differ on current watchOS; do not reset, unpair, or introduce MDM as an automatic workaround.

## P1：AQI量尺卡片相容性

現有CWA LinkedAPI AQI寫入`TAIWAN_AQI`後，原生App再取 `/api/v1/airQualityScale/zh-Hant-TW/TAIWAN_AQI` 得404。scalar/root解碼成功只驗證數值，完整卡片尚未修復。下一步：擷取支援的scale response、解析protocol與分類文字/顏色/區间，實作正確台灣量尺端點與對照測試，最後Mac與iPhone UI驗收。不要重標其他國量尺作為臺灣量尺的捷徑。

## P2：氣象語意与地理代表性

- PoP按等事件率與獨立增量拆時窗屬未校準推估；雨量均勻拆分無法知道分鐘起停。需要留來源並進行獨立準確度評估。
- 06–翌06日夜高低溫與Apple曆日不同；當前观測偶爾超過預報最高、圖示與保留比較摘要可能矛盾，需資料語意一致性設計。
- 最近鄉鎮代表點、水平距離測站配對，邊界與山區需要多邊形/海拔/地形改善。
- 目前溫度採格點分析時仍可能沿用測站observationTime/asOf，需複核各欄位來源時間的UI語意。

## P2：運行維護

- WRF APCP固定byte offset、pressure尾部估算對現格式有效；新增動態message索引較穩健，現有強檢查與fail-safe應保留。
- TLS leaf續期與CA續期尚為人工；整機/Tailscale/Apple上游離線未纳入3.5秒翻譯fallback，外部監控可獨立設計。
- 原生協定未知slot、新OS版本須重新驗證；保留的Apple字段與圖磚整合逐項研究。
- `configurationReady`只整合目前route/DNS條件；Use-with-exit旗標目前歷史快照，而非每分鐘live核對。
- repo中的Linux unit、IP與部分ROOT硬編碼，獨立host配置／本機runtime參數化尚未實作。現有production metadata package.json0.2.0已在Mac repo校正，正式source尚未變更。

## 驗證仍需分開進行

iPhone每個Exit Node、Wi-Fi↔行動網路、不同網路漫遊；原生AQI與其他新增卡片UI；全機重開機／斷線恢復；長時間運行與通知實際手機接收。不要因某一個Mac模式通過宣稱全部組合已驗。

## 排除項目

**jarvis：使用者在本次repo交接前已明確指示略過，主機本身有問題。** 保留既有失敗證據，對其進一步探測／修復需使用者重新提出。

## 文件／版本陷阱

`docs/history`與`.private`內保留舊pending/舊規則，現在狀態由HANDOFF与live source判讀。剛建立Git repo的snapshot不是自動部署管線；正式Pi5跟Mac source後續可能分岔，deploy先比hash。
