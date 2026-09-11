# 完整交接狀態

## 使用者目標與工作邊界

Jamie 偏好 Apple iOS／macOS 內建天氣的 UI，希望臺灣核心氣象資料採 CWA。正式中轉放在 Pi5，裝置透過 Tailscale + AdGuard，安裝並完整信任限定 WeatherKit 的 CA。操作用 Executor MCP 於對話完成，保留真實實驗與失敗，不把測試腳本通過等同 UI 已驗收。

本次任務：在 Mac `~/cwa-apple-proxy/` 建立完整程式與文檔 Git repo，方便未來 AI 接手。**jarvis 節點不再排查**，使用者已明示該主機本身有問題。

## 現在有效的狀態

| 項目 | 狀態與證據 |
|---|---|
| CWA 資料轉換 | 正式 0.3.1；程式常數、健康端點與 production manifest 可核對 |
| 傳輸 | 1.0.2；已完成任意正常 Exit Node 共存的設定與代表節點測試 |
| CA | 名稱 CWA Weather Bridge Root；限 weatherkit.apple.com；私鑰留 Pi5 |
| Mac | 100.122.163.78，已啟用、原生 App / Widget 曾成功；出口測試後還原 None |
| iPhone | 100.123.14.68，tailnet 名稱 localhost 就是 iPhone 14 Pro；已啟用，原生 iOS Weather / Widget 均已取到改寫回應 |
| DNS | 四個 restricted domain -> 100.78.140.101，四條 Use with exit node 已存並做出口切換測試 |
| 子網路 | 4 條 Apple relay specific routes 已宣告、控制端核准、Mac 收到 |
| Pi5 原有功能 | 192.168.31.0/24 LAN 宣告與可當 Exit Node 的廣告保留；既有 HTTPS 首頁及 Runpod 路徑保留 |
| jarvis | 曾公網探測失敗；最新使用者指示為略過，不屬待修本專案項目 |

**歷史覆寫規則：** 0.2.0 報告中「降雨機率保留 Apple」已由 0.3.1 推估實作取代；1.0.0「路由 pending」已由 1.0.1 核准後驗收取代；早期 iPhone pending 已由 iPhone 實測取代；「Exit Node 必須 None」已由 1.0.2 共存取代。歷史檔案保存原內容，現在狀態以本頁＋即時檢查為準。

## 驗收基準

- 0.3.1：368 鄉鎮核心查詢通過；AQI 有效覆蓋 367；1,000 次 FlatBuffers 本機重播通過，中位 89.27 ms、p95 183.34 ms。屬当時測試，不等同每筆即時資料必定完整。
- Mac 基礎 16 份原生 App / Widget 封包逐欄位核對通過。
- iPhone：2026-09-11 16:18–16:21，2 份 Weather + 1 份 Widget，2,160 個改寫欄位核對通過；臺南 Apple 30.02°C -> CWA 28.8°C，翻譯 1,383 ms。
- Exit 共存：None、Pi5、A1-JP、A1-US、Mullvad jp-tyo-wg-001、us-lax-wg-402 均有新原生 Weather 回應；12 份封包、10,846 個改寫欄位通過。測試主機為 Mac；iPhone 逐出口切換仍未實測。
- 正式既有單元測試 76 Python + 23 Node = 99。本 repo 額外的結構與來源檢查獨立計數。
- 3.5s 隔離故障：3.5045 秒退回 Apple 原始壓縮內容及標頭；ntfy HTTP200，收據 HjQlUd89Xw7f。代表伺服器接受測試通知，手機呈現另驗。

## 接手後的首個具體功能工作

AQI 是確定的既有相容性缺口：mapper 已寫入 `scale=TAIWAN_AQI`，App 接著請求 `/api/v1/airQualityScale/zh-Hant-TW/TAIWAN_AQI`，現有上游回 404，卡片呈現待修。
建議先解析真實已支援的 scale 端點格式，再實作該量尺的正確回應／資料映射與測試，驗證臺灣 AQI 分類和原生 UI。保留污染物單位，避免用名稱替換掩蓋量尺差異。
其餘工作見 KNOWN_ISSUES；本次 repo 建立不順便修資料算法或改正式部署。

## 證據與歷史在哪裡

`docs/evidence/production-source-manifest.json`：來源與本次初始拷貝的 SHA。`infra/snapshots/`：本次唯讀主機快照。
`docs/history/`：原版報告；`docs/reference/`：API YAML、GraphQL schema、GRIB 參數、Apple accessor 研究。
`tools/history/`：全部收集到的自訂研究／部署修補脚本，僅供閱讀；已遮蔽 CWA key。
`.private/history.tar.gz`：更完整的原始研究、日誌、報告；`.private/native-evidence.tar.gz`：裝置／原生封包證據；`.private/provenance/history-manifest.json`：省略項目與原因。
`docs/evidence/repo-verification.json`：本 repo 最終測試與 commit 前核對；後續需帶新的 timestamp。

保留失敗：Mac Executor 多次502、terminal base64輸出、短觀察窗受 App 快取影響、初始 IPv6 缺出口、UDP burst 偶發限速／丟包、猜測 relay Host 導致 TLS 名稱不符、npm 私有 package 拉取失敗、requirements 原鎖缺 eccodes 等，均已列於對應文件或歷史中。
