# 已知問題與待辦

## Corrected/guarded in 0.3.2: temperature and precipitation audit findings

The bridge must not be described as error-free weather or a complete copy of official CWA values. The [0.3.1 audit evidence](evidence/correctness-20260920.json) is historical; [0.3.2 acceptance](evidence/accuracy-032.json) records the applied corrections.

- Daily extrema now use a complete 00–24 hourly sample set (plus today's validated observations) and update both occurrence times. Missing coverage retains the entire Apple extrema family. Sampled extrema remain a derived forecast, not exact continuous-time extrema.
- Rainfall totals update only compatible rain-only companions; unsupported/multiple/snow phases retain Apple. Apple phase classification is explicitly mixed-source rather than falsely attributed to CWA. Tests cover top-level phase conflicts and nonzero snow intensity.
- PoP only uses an identical, non-conflicting official interval. Unmatched hourly/daily values remain Apple; the 3h/12h hazard model is removed from live conversion.
- Rainfall is no longer fractionally split or radar/model blended. Trace `T` remains nonnumeric. The next-hour QPF is only usable for its exact source window.
- Current thermodynamics stay with one station/time; grid analysis is diagnostic-only. Missing/inconsistent thermodynamic groups retain Apple. Hourly temperature-related groups use exact same-time source points, not interpolation.

Remaining limits: native coverage is intentionally lower for incompatible precipitation windows and long-horizon temperatures; daily extrema depend on sampled hourly forecasts and spatially representative station/town data; Apple comparisons, summaries and other unmapped fields may still describe Apple's forecast. There is no calibrated new disaggregation model or validated +78/+84h extension. A new physical iPhone/Watch UI check for 0.3.2 remains separate from Mac/replay validation.

## Resolved: Apple Watch Weather and custom CA trust

The user installed the custom CA on Watch and confirmed Weather recovery with iPhone Tailscale enabled. The subsequent server audit identified four successful Watch responses. Apple requires installing a custom CA on both paired devices ([QA1948](https://developer.apple.com/library/archive/qa/qa1948/_index.html)). Controlled `unknown-ca` probes are not device evidence. No routing workaround was needed.

Keep existing iPhone/Mac enrollment and routing intact. Installing a certificate on iPhone alone is not Watch acceptance. Do not reset, unpair, or introduce MDM as an automatic workaround.

## P1：AQI量尺卡片相容性

現有CWA LinkedAPI AQI寫入`TAIWAN_AQI`後，原生App再取 `/api/v1/airQualityScale/zh-Hant-TW/TAIWAN_AQI` 得404。scalar/root解碼成功只驗證數值，完整卡片尚未修復。下一步：擷取支援的scale response、解析protocol與分類文字/顏色/區间，實作正確台灣量尺端點與對照測試，最後Mac與iPhone UI驗收。不要重標其他國量尺作為臺灣量尺的捷徑。

## P2：氣象語意与地理代表性

- 0.3.2 已停用未校準 PoP／雨量拆分；新增衍生模型仍需獨立預報準確度驗證，不能以守恆測試取代。
- 0.3.2 已修正曆日時段與極值時間；保留 Apple 的其他圖示／歷史比較摘要仍可能與 CWA 資料不同。
- 最近鄉鎮代表點、水平距離測站配對，邊界與山區需要多邊形/海拔/地形改善。
- 0.3.2 的格點溫度僅供診斷；若未來重新採用，必須先解決完整溫濕度組與時間／空間代表性。

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
