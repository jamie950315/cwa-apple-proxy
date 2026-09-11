# 檔案来源與保留範圍

來源權威：本次唯讀擷取Pi5 `/home/jamie/cwa-weather-proxy`。`evidence/production-source-manifest.json`記錄初始拷貝source path、SHA256、長度與遮蔽旗標。
功能.py/.mjs保持正式位元組；README、package metadata、developer scripts、完整依賴鎖與交接文檔是Mac repo新增／整理，不會自動改正式部署。

## 分層保存

| 路徑 | 範圍 |
|---|---|
| 根目錄功能程式、vendor、tests、systemd、config | 正式完整程式與必要配置／測試，少量即時狀態採example |
| infra/live-systemd | systemctl cat取得的已安裝unit；需與source unit區分 |
| infra/snapshots | 本次service、Serve、route、DNS、nft與dependency freeze快照 |
| docs/reference | 官方API YAML／LinkedAPI schema／GRIB及原生codec研究 |
| docs/history | 原始部署與驗收報告，維持當時內容 |
| tools/history | 歷史研究與一次性修補脚本，供讀碼追溯，全部標為非自動操作入口 |
| .private/history.tar.gz | 原始研究文字、日誌、schema、早期失敗與報告 |
| .private/native-evidence.tar.gz | 可用裝置原生bytes、mapper報告、CWA snapshot等 |
| .private/runtime | 當時clients/managed DNS/路由ownership狀態與public CA |
| .private/provenance/history-manifest.json | 歷史封存檔案hash、遮蔽及省略理由 |

省略的是可重建的環境`.venv`/node_modules、.git、暫存PID、大型GRIB原始下載與秘密設定備份；這些仍在Pi5原本位置。GRIB重新取得方法見model_worker與official schema。原生proof有原先20組滾動保留限制，本次只能封存當時仍存在的檔案，已有被滾掉的原始資料不宣稱完整復原。

本次沒有原始ChatGPT對話逐字稿匯出，HANDOFF/DECISIONS/CHANGELOG保留可見對話的技術決策與修正，搭配實際檔案與測試證據。後續AI以具體內容與新的live驗證接續。
