from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/dashboard.html');s=p.read_text()
s=s.replace('<small>0.2.0</small>','<small>0.3.0</small>')
start='<section><h2>資料對應範圍</h2>'
end='<section><h2>查驗 CWA 原始時間區間</h2>'
a=s.index(start);b=s.index(end,a)
new='''<section><h2>資料對應範圍</h2><p><strong>目前溫度優先使用 CWA O-A0038-003 每小時地面溫度分析格點</strong>；濕度、風向、風速、氣壓、陣風與天氣現象使用鄰近 CWA 測站，露點由 CWA 溫度與相對濕度計算。能見度使用最近可用的 CWA 綜觀站能見度級距並換算公尺。</p><p><strong>降雨觀測與短延時預報均來自 CWA：</strong>O-A0002-001 提供 10 分鐘、1／3／6／12／24 小時累積雨量；F-B0046-001 提供雷達外推的未來 1 小時 QPF。CWA 官方 3 小時與 12 小時降雨機率會依來源時段轉成 Apple 逐時欄位；3 小時機率採等風險拆分，使三個逐時機率重新合成後仍等於 CWA 原始 3 小時機率。診斷紀錄會標示「CWA 衍生值」。</p><p><strong>每日高低溫採 CWA 完整白天＋夜間時段，通常為 06:00 至隔日 06:00。</strong>逐時溫度、露點、濕度、體感與風速以 CWA 原始預報點為主，最多 3 小時內只對連續數值做線性內插，不外插。</p><p>仍保留 Apple 的欄位會逐項列入診斷：目前包括雲量分層、CWA 公開資料未直接提供的部分未來 6／24 小時連續雨量、Apple 特有的歷史比較／預報變更／新聞，以及尚未完成 WeatherKit 根節點重建驗證的空氣品質與警特報。天文資料 API 目前公開資料內容仍是 2025 年表，因此暫不注入 2026 原生天氣。</p><p><strong>任何 CWA 連線、資料驗證、FlatBuffers 轉換失敗，或整體翻譯超過 3.5 秒，都立即回傳 Apple 原始資料，並非同步通知 <code>ntfy.sh/cwa-apple-proxy</code>。</strong>同類錯誤 5 分鐘內只通知一次，避免洗版。</p></section>'''
s=s[:a]+new+s[b:]
s=s.replace("`${s.location.county} ${s.location.forecastTown||s.provenance.forecastDatasets?.[0]?.town||''} · ${s.current.temperature}°C · 測站 ${s.location.stationName}，距離 ${s.location.stationDistanceKm} km`","`${s.location.county} ${s.location.forecastTown||''} · ${s.current.temperature}°C · 測站 ${s.location.stationName}，距離 ${s.location.stationDistanceKm} km · 過去1h雨量 ${s.rain?.past1h??'—'} mm · 未來1h QPF ${s.nowcast?.amount??'—'} mm`")
p.write_text(s)
