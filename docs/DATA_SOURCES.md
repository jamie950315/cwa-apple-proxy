# 資料來源、單位、時窗與地理選擇

本表描述 0.3.2；來源、時間及相關欄位相容才改寫，缺口保留 Apple。官方、衍生與混合來源以 assignments/sourceCoverage 區分；計數含數值未變的有效賦值，不代表整包資料覆蓋率或天氣零誤差。

## Source audit — 2026-09-20

The proxy starts from an Apple native response; it is not a complete replacement weather provider. Overrides apply only to supported Taiwan requests, valid source times and locations, and complete forecast windows. Availability varies per response, so there is no fixed percentage of CWA versus Apple data.

- Current apparent temperature retains Apple. Hourly apparent temperature uses exact source points only. Station dew point, sea-level pressure and visibility category values remain explicitly derived; intensity and split-period PoP derivations are no longer applied.
- The entire minute-by-minute `forecastNextHour` root remains Apple. CWA radar QPF contributes one-hour totals to other fields; it does not generate a minute-by-minute start/stop curve.
- AQI is originally measured/published by Taiwan MOENV and transported through CWA LinkedAPI. It is not an independently measured CWA AQI. Valid AQI replaces the AQI root; its separate `TAIWAN_AQI` scale endpoint still returns 404 and remains a known UI limitation.
- Valid CWA warning detail is merged with non-CWA Apple alerts. It does not remove every Apple warning. The unused W-C0033-001 summary download was removed; W-C0033-002 remains authoritative for this integration.
- Astronomy replaces only the mapped event times. Moon phase/illumination and nautical/astronomical twilight remain Apple. Unknown native roots/slots and source coverage gaps remain Apple.
- This audit checked the actual mapper and snapshot normalization, rather than assuming every field present in a CWA response is written into the App. See [performance and cache behavior](PERFORMANCE.md) for the independent fetching changes.

| 欄位 | 來源 | 轉換／界線 |
|---|---|---|
| 即時氣溫、濕度、風速風向 | O-A0001-001 / O-A0003-001 | 最近有效測站；風 m/s -> km/h、濕度 API fraction -> WK scalar % |
| 空間溫度分析 | O-A0038-003 | 僅診斷保留，不單獨替換測站溫度組 |
| 逐時體感／溫度／濕度／露點／風 | F-D0047-xxx | 僅原始同時刻點；溫濕度組必須完整且物理一致，不內插 |
| 目前露點 | 同測站觀測溫濕度 | Magnus 公式推估；不以不同時間預報補入同一組 |
| 每日高低溫 | 今日 DailyExtreme＋剩餘逐時點；未來完整日逐時點 | 僅00:00–24:00完整樣本範圍；同步更新極值時間，明示衍生，非官方連續時段極值 |
| 天氣圖示／代碼 | 觀測文字／F-D0047 | 晴、多雲、陰、雨、雪、雷、霧等映射；未知保留Apple |
| UV | 有效測站／F-D0047每日 | 當前與maxUvIndex；每小時UV曲線尚待整合 |
| 過去雨量 | O-A0002-001 | 與current.asOf同時刻且附帶欄位相容才覆寫；T僅列traceFields，不造出0.05mm |
| 目前雨強 | Apple | 不再把十分鐘平均速率當作瞬時雨強 |
| 未來一小時QPF | F-B0046-001 | 雷達外推格點，保留起報及有效時段；格點座標近似另記 |
| WRF定量降水 | M-A0064, WRF3km | 同起報APCP累積差分成6h；取+6到+72h；驗證lead與時間相符，不混接radar |
| 逐時／每日雨量 | 時段完全對齊的雷達或同起報WRF | 完整且不重疊的原始時窗才可加總；不切割。單一rain-only分類可保留Apple，總量及expected同步，明示mixed來源；其他相態保留Apple |
| 降雨機率 | 完全吻合的官方原時段，否則Apple | 不拆分、不合成；同時段多個官方值衝突時保留Apple |
| 氣壓 | 觀測+高度／WRF海平面 | 測站pressure與海平面pressure區分；溫濕度／海拔換算屬推估；WRF最多6h內插 |
| 現在陣風／能見度 | 新鮮測站 | 陣風時間約30m內；能見度級距代表值，開放級距採下界；缺值保留Apple |
| AQI／污染物 | CWA LinkedAPI 原始環境部 | 臺灣AQI；CO ppm -> ppb；量尺端點相容性仍待修 |
| 警特報 | W-C0033-002 | 有效期／區域篩選，與Apple原警報合併；失敗保留原root |
| 日出／日落／過中天／民用曙暮／月出月落 | A-B0062-001 / A-B0063-001 | 當年度日期篩選，縣市代表點按本地日期匹配 |

## 仍保留 Apple

未對齊的逐時／全天機率、無法完整映射的雨量與極值組、目前體感／瞬時雨強、分鐘級降雨起停／曲線、天氣地圖圖磚與動畫、總／分層雲量、預報陣風／能見度、逐時UV、氣壓趨勢、相態與降雪深度／降水機率分布細項、月相／照明率、航海及天文曙暮光、新聞／歷史基準比較／變化摘要、未知私有協定slot、CWA時空缺口與臺灣以外城市。
這表示本版本的整合範圍。其他官方產品的可用性與對應關係仍可研究，不能以保留Apple直接斷言CWA沒有該資料。

## 定位

App使用裝置位置或搜尋城市座標。代理從 URL 讀 latitude/longitude，按country=TW与20–27N、117–124E邊界處理。Exit Node 的公網IP不參與此座標選取。
核心觀測從30km內、90m內更新、有有效氣溫的最近站挑選；雨量另選30km/30m，能見度50km/90m；容許未來5m時鐘誤差。
鄉鎮由368代表點選最近者，上限60km；屬近似對應，行政區邊界／山區海拔代表性仍待精化。WRF使用預先計算的鄉鎮格點。AQI／天文使用各自空間條件，查看來源distance與站名。

## 已知方法風險

PoP非唯一可逆拆分，0.3.2僅保留原時段匹配，不再使用未校準拆分。完整逐時樣本的日極值仍是衍生預報，不能保證連續時間中沒有更高／更低值。
目前資料混合可能造成當前觀測高於今日預報最高溫、即時weatherCode與舊Apple比較文案不一致。處理時需保留觀測／預報語意，不可無據改數字求表面一致。
WRF Range offset（APCP固定offset與pressure尾部推算）依目前檔案布局；已有 GRIB magic、長度、parameter、step、level、ETag驗證，布局變更會被拒絕，未實作完整動態索引。

## 官方資料研究快照

`reference/openapi-current.yaml`、`reference/linked-aqi-schema.json`、`reference/grib-parameters.json` 與 `reference/catalogue-audit.json`。
REST: https://opendata.cwa.gov.tw/api/v1/rest/datastore/ ; File: https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/ ; LinkedAPI: https://opendata.cwa.gov.tw/linked/graphql 。舊快照按取得日期解讀，新增功能前重查官方介面。
