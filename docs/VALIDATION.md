# 驗證證據與可聲稱範圍

| 階段 | 已存在的證據 | 限制 |
|---|---|---|
| CWA取數 | 觀測、F-D0047、雨量、QPF、WRF、天文、LinkedAQI成功取數 | 依各自更新時間及範圍，欄位可能部分缺值 |
| 0.3.1資料層 | 368/368鄉鎮；AQI367；1,000/1,000重播 | 本機重播與手機UI分開 |
| Mac真實封包 | 原先16份逐欄位通過 | AQI自訂量尺卡片仍404 |
| iPhone | 2 Weather+1 Widget；2,160改寫欄位通過 | 已證明HTTPS與回傳bytes；各卡片UI、每個出口另驗 |
| 免Exit Node | 1.0.1四路由核准、四restricted DNS；13傳輸檢查+95回歸 | 限受測Mac網路；IPv6無公網出口採快速回退 |
| 1.0.2共存 | 正常6種出口模式，12真實回應、10,846欄位核對；99回歸 | 部分40s無新回應後用新城市補測；jarvis依使用者略過 |
| timeout/ntfy | 3.5045秒、Apple原始壓縮body/header保留、ntfy200 | 測試為隔離故障；NTFY伺服器收件與手機通知另分 |

原版本報告保留於`history/`；精簡機器證據於`evidence/`；原始native檔在`.private/native-evidence.tar.gz`與Pi5 reports各資料夾。

## 新一輪真機驗收應保留

時間（Asia/Taipei）、裝置與App UA、ExitNodeID、系統DNS、route、服務health、Apple原bytes、CWA來源與時窗、mapped bytes、report changes、原生UI截圖／卡片結果。
逐筆getter比對final mapped values與report.after／snapshot來源。浮點容許誤差明確限定；數值相等而沒改寫不計入modifiedFields。
確認測試開始至結束出口一致，回復原來客戶端設定；現有城市可命中快取，適度查新城市。

## 此次repo交接的驗證

來源manifest檢查正式所有功能.py/.mjs保持原內容；可攜性／文檔／metadata調整另列。
在Mac隔離環境跑既有Python/Node測試；在Pi5再跑同一組基準作對照；新增文件連結、必要fixture、秘密掃描、tracked檔案檢查。
結果填入`evidence/repo-verification.json`，其中平台、時間、exit code與測試數分開。任何失敗保留原始日誌及原因。
