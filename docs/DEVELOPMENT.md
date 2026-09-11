# 開發與依賴

## 版本快照

Pi5：Python3.13.5，實際freeze在`infra/snapshots/python-freeze.txt`。Mac來源環境：Python3.14.7、Node23.11.0；repo bootstrap使用隔離Python3.13以接近正式環境，具體結果見repo-verification。
`requirements.production-linux.lock`為正式環境完整freeze，包含舊requirements.lock缺少的eccodes/eccodeslib/eckitlib/numpy/pyproj/findlibs。
`requirements.development.lock`以相同實測版本加上Linux限定套件條件，macOS由套件管理器選對應平台wheel。`requirements.lock`保存舊來源鎖供對照，重建優先新完整鎖。
Node執行依賴已封裝在vendor，无外部runtime npm dependency。來源package.json metadata曾停在0.2.0；本repo校正為資料版本0.3.1，傳輸版本分開記於versions.json。Pi5原檔保持原樣。

## 測試

```sh
./scripts/bootstrap-dev.sh
./scripts/test.sh
python3 scripts/verify_repo.py
```

測試不需真實CWA key；httpx mock與固定歷史時間驗證資料映射。少量fixture維持原本`research/actual-brief.json`與其引用FlatBuffer路徑，該城市座標為既有固定測試樣本。完整裝置查詢位置保存在`.private`。
`tests/mapper.test.mjs`驗證單位、3h內插、完整日夜pair、PoP推估、未知root與省略scalar保留、警報/天文、malformed rejection。
`tests/test_addon.py`驗證非目標流量、壓縮回應、錯誤body/header保留、deadline與通知去重。`tests/test_split_routes.py`／`test_exit_compatibility.py`涵蓋範圍驗證與核准語意。

## 本機執行限制

本次交接保留正式功能程式位元組，沒有順帶改寫所有ROOT／bind。Python主要資料模組採檔案相對ROOT；addon仍固定正式Pi根目錄與API網址。`codec_server.mjs`固定loopback18881。`/status`需要本機CA public file，`Store`讀取根目錄.env，即使設了環境變數也仍會先讀該檔。
因此本機預設只跑離線測試與讀文件；正式完整runtime在Pi5。將服務泛化為本機可獨立啟動屬後續重構，不要用symlink建立假的`/home/jamie`或直接套Linux unit到Mac。

## 更新fixture與codec

重新擷取原生App、驗證Country/MIME、移除auth與個人位置後，挑固定城市fixture。測試期固定`now`，避免使用舊觀測被程式判stale。同時保存原始bytes、normalized CWA、mapper report與request metadata。
Vendor修改保留LICENSE/NOTICE，更新来源hash與重建方法。當AQI或alerts重建root時，要重新驗證unknown slot與siblings未損傷。

## Git

本repo初始化main branch，使用已有本機Git identity；預設不建立remote、不push。
`git config core.hooksPath .githooks`安裝repo內secret掃描pre-commit。自行clone後可重新設置hook。
`.private`、.env、certs、runtime cache、node_modules、.venv與log排除。`git status --short`應只反映真實待提交變更。

## Mac 實測平台依賴

首次安裝發現正式Linux鎖的 eccodeslib 2.48.2.27 僅有Linux wheel。development鎖將eccodeslib/eckitlib的該版限定Linux，Mac交由同版eccodes binding選相容二進位，再保存完整requirements.macos.lock。
本次Mac實測：Python3.13.5、ecCodes binding2.48.0、eccodeslib2.48.0.26、eckitlib2.1.1.26；`python -m eccodes selfcheck`確認libeccodes.dylib成功載入。bootstrap在Mac優先使用本次驗證的requirements.macos.lock。
官方安裝機制來源：https://github.com/ecmwf/eccodes-python 。舊的Linux-only lock安裝失敗日誌保留在.private/macos-initial-dependency-failure.log。
