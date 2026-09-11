# CWA Apple Proxy

使用 Pi5 中轉 Apple 原生天氣的 `WK2.Weather` FlatBuffers，把有效範圍內的臺灣天氣數值替換成中央氣象署資料及有註明方法的推估。保留 Apple 原生 UI、其餘資料及翻譯錯誤回退。

| 項目 | 目前狀態 |
|---|---|
| 本機 repo | `/Users/jamie/cwa-apple-proxy` |
| 正式部署 | Pi5 `/home/jamie/cwa-weather-proxy` |
| 資料層／傳輸層 | `0.3.1`／`1.0.2` |
| 已啟用裝置 | Mac `100.122.163.78`、iPhone 14 Pro `100.123.14.68` |
| Exit Node | 可选 None、Pi5 或其他正常節點，天氣維持 Pi5 分流 |
| 診斷頁 | `http://100.78.140.101:18880/`，需 Tailscale |
| 故障通知 | `ntfy.sh/cwa-apple-proxy`，翻譯逾時 3.5 秒、同原因 300 秒去重 |
| 已知主要缺口 | `TAIWAN_AQI` 量尺端點 404，完整 AQI 卡片待處理 |
| 本次範圍外 | jarvis 主機問題，依使用者指示略過 |

## AI 接手

從 [AGENTS.md](AGENTS.md) 與 [完整交接狀態](docs/HANDOFF.md) 開始。技術決策、已驗證範圍、失敗紀錄與下一步均有保留。原始對話逐字稿未另行匯出；文件是依當前對話與主機實際程式、研究及驗收檔案整理的技術交接。

## 本機驗證

```sh
cd ~/cwa-apple-proxy
./scripts/bootstrap-dev.sh
./scripts/test.sh
python3 scripts/verify_repo.py
```

Python 環境安裝在 repo 的 `.venv`。Node 使用內建 test runner 與 vendor codec，無需 npm 網路下載。測試使用本地歷史 fixture 與 mock；實際 CWA API key 維持在 Pi5。

Mac 用於開發、閱讀與測試；正式服務使用 Linux systemd、nftables 與 Tailscale Serve。程式保留來源版本的正式位址與部分絕對路徑，搬移／本機啟動服務前請先讀 [開發環境](docs/DEVELOPMENT.md)。

## 文件索引

| 文件 | 用途 |
|---|---|
| [HANDOFF](docs/HANDOFF.md) | 現在狀態、使用者決策、驗收界線、閱讀順序 |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | 封包、服務、來源與 port 資料流 |
| [DATA_SOURCES](docs/DATA_SOURCES.md) | CWA／Apple 欄位、時間解析度、推估語意 |
| [NETWORKING](docs/NETWORKING.md) | DNS、Exit Node 共存、IPv4／IPv6 與 opt-in |
| [OPERATIONS](docs/OPERATIONS.md) | 健康檢查、部署、備份、回復、憑證維護 |
| [DEVELOPMENT](docs/DEVELOPMENT.md) | 依賴、fixture、離線測試及固定路徑限制 |
| [VALIDATION](docs/VALIDATION.md) | 各版本的實測數字與證據層級 |
| [KNOWN_ISSUES](docs/KNOWN_ISSUES.md) | 未完成項目與優先順序 |
| [DECISIONS](docs/DECISIONS.md) | 架構選擇及捨棄方案的理由 |
| [SECURITY](docs/SECURITY.md) | 憑證、位置紀錄、金鑰與分享邊界 |
| [PROVENANCE](docs/PROVENANCE.md) | 正式檔案 SHA、歷史檔案與私有封存索引 |
| [CHANGELOG](docs/CHANGELOG.md) | 功能演進與本 repo 交接修改 |

`systemd/` 為來源部署檔；`infra/live-systemd/` 保存實際已安裝的 unit 快照，以便比較差異。`docs/history/` 保存各版本原報告，內容按其日期解讀。完整研究及位置證據另存於 `.private/`，Git 會略過。

## 授權

原始專案 `package.json` 的自訂程式授權維持 `UNLICENSED`，repo 保持 private/local。vendor codec 的 Apache-2.0 授權與來源 NOTICE 已原樣保留於 `vendor/`。第三方研究參考各維持原授權；本 repo 未額外授予整體公開散佈授權。
