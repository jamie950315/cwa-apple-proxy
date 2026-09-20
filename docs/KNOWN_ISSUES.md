# 已知問題與待辦

## P1: Temperature and precipitation correctness audit failed (2026-09-20)

The bridge must not be described as fully correct or as a direct copy of official CWA values. Read [the audit evidence](evidence/correctness-20260920.json) before changing these mappings.

- Live: 120 daily windows in 20 retained proofs use CWA 06:00–next 06:00 extrema in Apple 00:00–24:00 days. Changed maxima/minima retain Apple's original extrema timestamps (120 of each). The current tests accept the shifted window; passing them is not semantic validation.
- Reproduced: changing precipitation scalar totals without their ByType companions can leave conflicting values in one native payload. The current 20-proof live sample had zero newly conflicting populated pairs among 114 checked; the bug is demonstrated by an existing native fixture, not asserted as present in that live sample.
- Reproduced: nested official PoP windows (12h 60%, nested 3h 50%) yield 74.8513% for the full 12h instead of retaining the source's 60%. Choosing the shortest overlapping interval and splicing independent hazards does not preserve official probability constraints.
- Uncalibrated assumptions: splitting 3h PoP into hourly probabilities, uniformly allocating 6h rainfall, and blending radar/model windows do not have a unique official answer. Trace `T` is mapped to an invented exact 0.05 mm. These must not be represented as exact official values.
- Conditional temperature inconsistency: replacing station temperature with a newer grid value retains station-derived dew point and station `asOf`; pressure provenance also describes station temperature while using the grid value. A constructed case yields temperature 20 C and dew point 30 C. The sampled live location did not use the grid override.

No mapper, runtime, or data policy changed during this audit. Decide the strictness contract before removing estimates or retaining more Apple fields. The recommended contract is to override only semantically aligned fields with compatible companion metadata; unsupported windows retain Apple rather than fabricate new official-looking values. This cannot guarantee forecast accuracy or exact conditions at the user's position.

## Resolved: Apple Watch Weather and custom CA trust

The user installed the custom CA on Watch and confirmed Weather recovery with iPhone Tailscale enabled. The subsequent server audit identified four successful Watch responses. Apple requires installing a custom CA on both paired devices ([QA1948](https://developer.apple.com/library/archive/qa/qa1948/_index.html)). Controlled `unknown-ca` probes are not device evidence. No routing workaround was needed.

Keep existing iPhone/Mac enrollment and routing intact. Installing a certificate on iPhone alone is not Watch acceptance. Do not reset, unpair, or introduce MDM as an automatic workaround.

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
