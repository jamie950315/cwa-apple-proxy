from pathlib import Path
import re
ROOT=Path('/home/jamie/cwa-weather-proxy');p=ROOT/'dashboard.html';s=p.read_text()
section='''<section><h2>Exit Node 相容模式 · 1.0.2</h2><p>裝置保持 Tailscale DNS 與子網路路由啟用；Exit Node 可選「無」，或選擇有正常網際網路出口及 tailnet 存取權的節點。天氣與指定 Apple relay 目的地維持經 Pi5，一般上網使用所選出口。</p><p>四個 Restricted DNS：<code>weatherkit.apple.com</code>、<code>tthr.apple.com</code>、<code>tether.edge.apple</code>、<code>tether.v.aaplimg.com</code> 皆指定 <code>100.78.140.101</code>，並已儲存「搭配出口節點使用」設定。</p><p id="networkState">讀取路由狀態…</p><p id="exitState">讀取最後一次出口切換驗收…</p><div class="scroll"><table><thead><tr><th>出口模式</th><th>一般網際網路</th><th>新原生回應</th><th>驗證結果</th></tr></thead><tbody id="exitRows"></tbody></table></div><p class="muted">此表代表最後一次 Mac 實測。管理頁 DNS 開關的確認時間、原生封包及還原結果獨立留存；iPhone 每一個出口模式仍需獨立驗證。共用 relay 目的 IP 的其他 Apple 流量也可能經 Pi5。個別出口連線故障需要另行處理。</p></section>'''
pattern=r'<section><h2>免 Exit Node[^<]*</h2>.*?</section>'
s,n=re.subn(pattern,section,s,count=1,flags=re.S)
if n!=1:raise RuntimeError('Expected one existing network section')
s=s.replace('Tailscale Exit Node 選 None／無，啟用 Tailscale DNS 與子網路路由，並完成上方管理端的 relay 路由核准及 DNS 分流。','Tailscale Exit Node 可選無或其他正常出口；啟用 Tailscale DNS 與子網路路由，上方四個天氣 DNS 已設定搭配出口節點使用。')
s=s.replace('Tailscale Exit Node 選 None／無，啟用 Tailscale DNS 與子網路路由；上方 relay 路由與 DNS 已設定完成。','Tailscale Exit Node 可選無或其他正常出口；保持 Tailscale DNS 與子網路路由啟用。')
start=s.find('const split=s.splitRoutes||{};')
end=s.find("$('changes').replaceChildren();",start)
# Preserve unrelated code between the existing transport summary and changes table.
if start<0:raise RuntimeError('Existing network JS missing')
end_statement=s.find(";$('changes')",start)
# Replace only the networkState assignment up to its terminating semicolon.
m=re.search(r"const split=s\.splitRoutes\|\|\{\};\$\('networkState'\)\.textContent=.*?;",s)
if not m:raise RuntimeError('Network state expression missing')
new="const split=s.splitRoutes||{};$('networkState').textContent=split.configurationReady?'Relay 路由與 Restricted DNS 配置就緒。':'請核對 relay 路由與 Restricted DNS 設定。';const compat=s.exitCompatibility||{};$('exitState').textContent=compat.verifiedAt?`最後驗收：${compat.verifiedAt} · Mac 原始出口已還原：${compat.macOriginalRestored?'是':'待確認'}`:'出口切換驗收資料尚未發佈';$('exitRows').replaceChildren();for(const x of compat.results||[])row('exitRows',[x.exit,x.ordinaryInternet?'正常':'探測逾時',x.nativeResponseCount??0,x.status]);"
s=s[:m.start()]+new+s[m.end():]
# Stop displaying obsolete phone pending instructions in any remaining prose.
s=s.replace('iPhone 名單仍為 pending','iPhone 已啟用並有原生回應驗證')
p.write_text(s)
# Validate script syntax separately using Node in the publishing step.
script=re.search(r'<script>(.*?)</script>',s,re.S).group(1)
(ROOT/'research/exit-compatible/dashboard-script.js').write_text(script)
print('Exit compatibility dashboard updated')
