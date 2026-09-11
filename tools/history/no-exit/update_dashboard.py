from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/dashboard.html');s=p.read_text()
marker='<section><h2>回退與 ntfy 通知</h2>'
section='''<section><h2>免 Exit Node 連線模式</h2><p><strong>裝置 Tailscale Exit Node 設為 None／無。</strong>保留 Tailscale 連線、DNS 設定與子網路路由。天氣 API 依裝置限定的 AdGuard DNS 規則連至 Pi5；一般網際網路保留原本的預設出口。</p><p id="networkState">讀取 relay 子網路路由核准狀態…</p><p>Pi5 已宣告四個 Apple relay 子網路：<code>17.253.0.0/16</code>、<code>2403:300:a00::/40</code>、<code>2620:149:a00::/40</code>、<code>2a01:b740:a00::/40</code>。到 Tailscale 管理頁的 Machines → Pi5 → Edit route settings 核准後，系統會分流這些目的地並對已加入名單的裝置拒絕 UDP/443，促成天氣 TCP 回退。</p><p>共用這些目的 IP 的其他 Apple 連線也可能經過 Pi5；其餘網際網路目的地維持既有路由。這些前綴涵蓋目前量測的 relay；換網路或 Apple 變更基礎設施後，仍需要確認涵蓋率。</p><p><strong>DNS 分流：</strong>Tailscale 目前有多個全域 DNS 伺服器。建議在管理頁 DNS 加入 restricted nameserver <code>100.78.140.101</code>，限定 <code>weatherkit.apple.com</code>、<code>tthr.apple.com</code>、<code>tether.edge.apple</code>、<code>tether.v.aaplimg.com</code>，維持原有其他 DNS 設定。這項管理端變更尚待完成。</p><p class="muted">Mac 於 Exit Node 關閉、系統代理關閉時已有原生中轉連線證據；完整 relay 分流驗收須以路由核准及新請求為準。iOS 裝置另需憑證信任與加入導流名單。</p></section>'''
if marker not in s:raise RuntimeError('dashboard insertion anchor missing')
s=s.replace(marker,section+marker,1)
s=s.replace('Tailscale Exit Node 選 Pi5，DNS 使用 Pi5 的 AdGuard。確認憑證信任後，於 Pi5 啟用該裝置：','Tailscale Exit Node 選 None／無，啟用 Tailscale DNS 與子網路路由，並完成上方管理端的 relay 路由核准及 DNS 分流。確認憑證信任後，於 Pi5 啟用該裝置：')
anchor="$ ('none')"
needle="$('fingerprint').textContent=s.certificateSha256;"
addition="const split=s.splitRoutes||{};$('networkState').textContent=split.relayRoutingReady?'Relay 子網路已核准；裝置仍須啟用子網路路由並正確使用 AdGuard DNS。':`Relay 路由待核准 ${(split.pending||[]).length} 條：${(split.pending||[]).join('、')}。DNS 直連模式可使用，跨網路 relay 分流待核准後驗收。`;"
if needle not in s:raise RuntimeError('dashboard state anchor missing')
s=s.replace(needle,needle+addition)
s=s.replace('分鐘級降雨起停／曲線、氣象地圖圖磚、總雲量與分層雲量、長時段定量降雨、逐時未接入的氣壓／陣風／能見度、','分鐘級降雨起停／曲線、氣象地圖圖磚、總雲量與分層雲量、超過有效 WRF 時窗的定量降雨與气壓、預報陣風／能見度、')
s=s.replace('CWA WRF 3 公里模式已完成 GRIB2 降雨及氣壓資料實驗；AQI 已取得 CWA LinkedAPI 的成功回應。這兩部分的原生欄位整合與驗收另列於稽核報告，避免把研究成功等同於正式啟用。','CWA WRF 3 公里 GRIB2 雨量／氣壓與 LinkedAPI AQI 已接入 0.3.1 翻譯層；AQI 自訂量尺的原生卡片顯示相容性仍待修正。封包驗證與畫面呈現分別記錄。')
p.write_text(s)
print('dashboard updated')
