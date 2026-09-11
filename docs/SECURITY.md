# 安全與資料邊界

本地Git repo以private專案處理，無Git remote。正式key在Pi5 `.env` 0600，CA私鑰在Pi5 `certs/ca-key.pem`及含leaf key的`certs/weatherkit.pem`。本次交接保持這些私鑰與實際key在Pi5原處，不複製進Mac source或Git。

Mac `.private`保存已遮蔽CWA key的原始研究／封包與public CA資料，mode0700、archive0600。位置、測站、client IP、原生回應與過往出口紀錄仍屬私有診斷；Git刻意略過`.private`。
`tools/history`文字中的CWA key已替換成`REDACTED_CWA_API_KEY`，原始hash記錄於provenance以供回查。少量測試fixture包含固定城市座標，目的是既有codec回歸，不含HTTP認證標頭。分享repo前仍需審查個人網路拓樸、copyright與研究引用。

CA限weatherkit.apple.com；葉憑證有效期約一年，需要維護。來源為已安裝且裝置信任的CA，既有CA不可因重建repo而自動換新。

CWA的TLS維持cert與hostname驗證；程式只關閉OpenSSL嚴格extension檢查以相容當時CWA chain。`verify=False`及`curl -k`不應變成正式取數預設。

ntfy topic為使用者指定public網址，通知不帶座標/API key/token。公開topic可被猜測；要控制訂閱/發送權限需另行設計。
`/status`含實際位置與proof、憑證fingerprint等資料，維持tailnet限縮，避免直接公開反代此診斷頁。

## 提交前

```sh
python3 scripts/verify_repo.py --staged
```

repo pre-commit會檢查實際stage bytes中的CWA key樣式、私鑰區塊與禁止路徑。`.gitignore`是一層保護，`git add -f`仍可能強加；hook與人工review共同使用。
