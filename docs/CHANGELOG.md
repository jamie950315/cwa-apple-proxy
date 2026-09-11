# 演進紀錄

## 2026-09-11：Mac repo交接

從正式Pi5抽取完整功能source、vendor、測試與實際systemd/Serve/DNS/nft快照，建立`~/cwa-apple-proxy`本機Git。
新增AGENTS及手動操作runbook、來源欄位表、歷史決策/已知限制、驗收manifest、bootstrap/離線測試/secret hook。
擷取完整production dependency freeze補上舊鎖缺少的GRIB/空間套件；package metadata在Mac校正為0.3.1，傳輸版本獨立1.0.2。正式Pi5程式、DNS、服務設定原樣保留。
使用者決策：jarvis略過。Mac建repo工具遇到Executor502，透過Pi5已知SSH通道續作。

## 1.0.2傳輸

四條restricted DNS開啟Use with exit node。None、Pi5、A1-JP、A1-US、兩個Mullvad代表出口有實際Weather新回應；12份/10,846字段核對，99回歸。Mac還原原設定。jarvis留失敗證據後依使用者略過。

## iPhone加入

使用者安裝信任CA後，將100.123.14.68加入IPv4/IPv6 opt-in；2原生App+1Widget實際回應，2,160欄位通過。server可見請求，不可由server直接知道客戶端選的Exit Node。

## 1.0.1傳輸

四條子網路核准後補四restricted DNS。IPv6無公網route時新增early QUIC與missing-FIB TCP快速回退；95回歸與13傳輸檢查。0.3.1資料功能維持。

## 1.0.0傳輸

由全流量Pi5 Exit Node轉為DNS+relay-specific routes；路由宣告與pending明確區分。Mac None模式App/Widget成功，控制端核准後才形成下一版驗收。

## 0.3.1資料

新增雨量站、官方溫度分析、1h radar QPF、WRF累積量差分、PoP推估、pressure/visibility/新鮮gust、天文與LinkedAQI、CWA警報、3.5s非同步ntfy。
擴充省略scalar、保留unknown root；PoP推估與均勻雨強假設可查核。AQI量尺卡片404仍待修。

## 0.2.0與協定研究

真實原生App的weatherkit API/v2、WK2.Weather FlatBuffers擷取、CA/SNI/Serve/AdGuard/Tailscale連接；最初溫度與鄉鎮預報替換。初期降雨機率保留Apple，後由0.3.1擴充。

### 本機實測補正

Mac完成99項既有回歸與ecCodes自檢。Linux-only二進位wheel與Mac版本分開鎖定；首次失敗保留.private，requirements.macos.lock記錄成功解析的67套件。
