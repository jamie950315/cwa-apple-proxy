# CWA Weather Bridge：iPhone 原生請求驗證

核實時間：2026-09-11 16:22:49（Asia/Taipei）。
資料翻譯層：0.3.1；傳輸層：1.0.1。
裝置：使用者的 iPhone 14 Pro；已加入 IPv4／IPv6 裝置限定導流名單。

## 已驗證結果

代理收到 3 筆真實 iOS 原生 HTTPS 請求，成功產生 CWA 改寫回應；重新解碼 3/3 通過，失敗 0。
User-Agent 分別為 `WeatherKit_Weather_iOS_Version 27.0 (Build 24A5430a)` 與 `WeatherKit_WeatherWidget_iOS_Version 27.0 (Build 24A5430a)`。

| 請求時間 | 來源 | CWA 測站 | Apple 原始氣溫 | 送回氣溫 | 改寫 scalar | 翻譯耗時 |
|---|---|---|---:|---:|---:|---:|
| 16:18:39 | iOS 天氣小工具 | 臺灣大學 | 27.89°C | 26.6°C | 357 | 152 ms |
| 16:19:18 | iOS 原生天氣 | 臺南 | 30.02°C | 28.8°C | 889 | 1,383 ms |
| 16:21:00 | iOS 原生天氣 | 臺灣大學 | 27.84°C | 26.6°C | 914 | 355 ms |

三筆 `skippedFields` 均為 0。這代表已列入改寫的欄位成功寫入；其餘保留 Apple 的範圍仍依混合資料政策處理。
臺南回應涵蓋 92 個逐時點、7 天資料，其中 154 個降雨相關欄位改寫。
三笔使用的核心測站觀測時間為 16:00；體感及其他推估欄位的來源、時間視窗另保存在各筆 cwa.json／report.json。

## 驗證方法

1. 由代理日誌篩選 iOS 原生 Weather／WeatherWidget 真實請求。
2. 將原始與改寫封包從輪替資料夾複製至獨立驗收資料夾。
3. 使用 WeatherKit FlatBuffers getter 重新讀取每個改寫欄位，與 report.json 目標值比對。
4. 核對氣溫及觀測時間、AQI 指數及量尺、CWA 警報 ID。
5. 確認 AdGuardHome、CWA API、代理及路由服務均為 active。

三筆合計重新核對 2,160 個 scalar 改寫。HTTPS 請求已到达代理，證明這些連線完成 TLS 握手；UI 每張卡片的最後呈現需獨立驗證。

## 使用狀態與限制

iPhone 啟用狀態已由 `enabled-awaiting-native-request` 更新為 `native-response-modified`。憑證安裝由使用者確認，原生 HTTPS 連線現已有實際證據。

使用免 Exit Node 配置時，裝置保持 Tailscale 連線、接受 Tailscale DNS 及子網路路由，Exit Node 選 None／無。Pi5 端可核對路由與 DNS 配置，手機當下 Exit Node 選項仍由裝置端管理；這份驗收未直接讀取手機的偏好設定。

原有 3.5 秒 CWA 取數／翻譯回退及 ntfy cwa-apple-proxy 通知程式維持原樣；這三筆均在期限內完成，未觸發翻譯失敗通知。

既有 `TAIWAN_AQI` 自訂量尺端點 404 與 AQI 卡片呈現問題仍為獨立待修項目。此驗收證明 AQI 數值已編入回應，UI 量尺相容性仍須另外修正。

## Pi5 證據

- `reports/iphone-onboarding.json`：啟用與原生請求狀態。
- `reports/iphone-native-audit.json`：逐欄位重新解碼結果。
- `reports/iphone-native/`：三份原始／改寫封包與 CWA 來源資料。
- `research/iphone-onboarding/audit_native.mjs`：本次驗收腳本。

診斷頁：`http://100.78.140.101:18880/`。
