# CWA Apple Proxy — AI 接手入口

## 先讀與目前目標

依序讀 `docs/HANDOFF.md`、`docs/ARCHITECTURE.md`、`docs/KNOWN_ISSUES.md`、`docs/OPERATIONS.md`。
再讀 `docs/evidence/repo-verification.json`（本 repo 的實測）與 `docs/evidence/production-source-manifest.json`（來源 SHA-256）。
本 repo 位於 Jamie 的 Mac `/Users/jamie/cwa-apple-proxy`；正式執行環境是 Pi5 `/home/jamie/cwa-weather-proxy`。這次交接建立的是本機 Git repo，GitHub remote／push 尚未建立。

資料翻譯版本 **0.3.1**；網路傳輸版本 **1.0.2**。Mac 與 iPhone 14 Pro 均已加入導流名單，iOS 原生 Weather／Widget 真實回應已驗證。
Exit Node 可選 None、Pi5 或其他正常節點。四條 restricted DNS 的 Use with exit node 已開啟；Pi5 的四條 relay 路由已核准。
**使用者最新決策：jarvis 主機有問題，略過該節點，維持現況。**

## 工作規則

- 使用繁體中文。每次續作以即時服務、程式與新證據核實狀態，舊報告保留其驗收日期。
- 此 repo 的建立不授權順便變更正式服務。程式修改、測試、部署各自記錄，部署需符合使用者當輪任務。
- 用 Executor Mac／Pi5 MCP 直接工作；使用者要求留在對話模式，無需轉交 Codex／其他工作模式。
- 探索工具一次後直接呼叫。terminal_output 的 `Data` 可能為 base64，解碼後讀取；也可將輸出寫成檔案再 filesystem_read。記錄 cursor，輪詢採有界次數。
- Executor Mac 發生 502 時，可透過 Executor Pi5 的已驗證 SSH `jamie@100.122.163.78` 操作 Mac。SSH 的 Safari JavaScript／Accessibility 權限有歷史限制；工具恢復後優先用帶 captureId 的桌面操作。
- 結果區分：設定已存／路由已宣告／控制端已核准／裝置已收到／HTTPS 通過／轉換完成／封包核對／原生 UI 顯示。各層需有各自證據。
- 成功封包的 `skippedFields=0` 僅描述本次可映射寫入；整包仍有刻意保留的 Apple 欄位。
- Watch recovery (2026-09-20): the user installed the CA on Watch and confirmed Weather works with Tailscale enabled; server logs subsequently showed successful watchOS transformations. Do not control the user's iPhone now that they have left the Mac at home. Keep iPhone/Mac enrollment intact. Initial controlled TLS probes are not Watch evidence; AdGuard logs are in `/var/log/adguard/`.
- Cache optimization (2026-09-20): Pi5 refreshes active dataset caches before expiry, without extending TTL/stale limits. Native bridge logs include Apple/CWA/codec/proof timings; they exclude device DNS/Bluetooth/rendering. See `docs/PERFORMANCE.md`; full Apple responses are not cached.
- 氣象推估保留來源、單位、時段、假設。PoP 時間拆分屬尚未校準的推估；時間內插維持現有限制。
- 保留 3.5 秒翻譯截止期限、Apple 原始位元組及標頭回退、非同步 ntfy 與 300 秒去重。
- 維持裝置 opt-in。完整信任 CA 後才 enable 新裝置；Mac、iPhone 已完成的啟用狀態不要回復成 pending。
- 密鑰留在正式 Pi5 `.env`／`certs`；Git 排除私鑰、原始位置紀錄與實際憑證材料。`.private` 包含本機研究證據，限本機使用。
- 此為私有原生 App 協定，更新 macOS／iOS 後重新擷取並驗證，未知 FlatBuffers slot 保持原內容。

## 安全入口

```sh
cd ~/cwa-apple-proxy
./scripts/bootstrap-dev.sh       # 只在 repo 建立 .venv
./scripts/test.sh                # 離線單元／封包 fixture 測試
python3 scripts/verify_repo.py   # 文件連結、來源完整性、秘密掃描
./scripts/pi-status.sh          # Pi5 唯讀健康檢查
```

`systemd/`、`bridgectl.py`、`network_rules.py`、`split_routes.py` 為 Pi5 Linux 維運工具；Mac 直接執行修改子命令會操作錯誤主機或失敗。維運步驟見 OPERATIONS。
`tools/history/` 是過去一次性研究／修補脚本，僅供閱讀；它們可能有固定舊路徑、破壞性覆寫或重新產生 CA 的行為。

完成實質工作後，更新 HANDOFF 的現在狀態、KNOWN_ISSUES、對應驗收 JSON／報告，以及 `docs/CHANGELOG.md`，再提交本機 Git。生產上傳與 push 各需符合使用者授權範圍。
