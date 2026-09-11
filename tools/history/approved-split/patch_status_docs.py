from pathlib import Path
import re,shutil,time
R=Path('/home/jamie/cwa-weather-proxy');b=R/'backups'/('status-docs-'+str(int(time.time())));b.mkdir()
for n in ['split_routes.py','dashboard.html','README.md']:shutil.copy2(R/n,b/n)
p=R/'split_routes.py';s=p.read_text();needle='def status():\n'
helper='''DNS_DOMAINS=['weatherkit.apple.com','tthr.apple.com','tether.edge.apple','tether.v.aaplimg.com']
def restricted_dns_status(text):
    found={}
    for line in text.splitlines():
        if ' -> ' not in line:continue
        left,right=line.strip().removeprefix('- ').split(' -> ',1)
        domain=left.strip().rstrip('.')
        if domain in DNS_DOMAINS:
            found.setdefault(domain,[]).append(right.strip())
    return {'domains':found,'requiredDomains':DNS_DOMAINS,
            'ready':all(found.get(d)==['100.78.140.101'] for d in DNS_DOMAINS)}

'''
assert needle in s;s=s.replace(needle,helper+needle,1)
needle="    advertised=prefs.get('AdvertiseRoutes') or []\n"
add="""    try:dns=restricted_dns_status(run(['tailscale','dns','status']))
    except (subprocess.SubprocessError,ValueError):dns={'ready':False,'error':'DNS status unavailable'}
    ipv6_probe=subprocess.run(['ip','-6','route','get','2403:300:a04:2000::61'],capture_output=True,text=True,timeout=5)
    ipv6_uplink=ipv6_probe.returncode==0 and 'unreachable' not in ipv6_probe.stdout and 'tailscale0' not in ipv6_probe.stdout
"""
assert needle in s;s=s.replace(needle,needle+add,1)
needle="'requiredClientExitNode':'None','requestedRoutes':desired,'advertisedRoutes':advertised,"
rep=needle+"\n            'restrictedDNS':dns,'ipv6UplinkAvailable':ipv6_uplink,'ipv6MissingUplinkBehavior':'Enrolled relay UDP rejected early; relay TCP reset only when the destination FIB route is missing. IPv4 TCP remains usable.',\n            'configurationReady':not a['pending'] and all(p in advertised for p in desired) and dns['ready'],"
assert needle in s;s=s.replace(needle,rep,1);p.write_text(s)
p=R/'tests/test_split_routes.py';s=p.read_text();s+='''\n\ndef test_restricted_dns_requires_all_four_exact_domains():
 from split_routes import restricted_dns_status,DNS_DOMAINS
 txt='\\n'.join('  - '+d+' -> 100.78.140.101' for d in DNS_DOMAINS)
 assert restricted_dns_status(txt)['ready']
 assert not restricted_dns_status(txt.replace('tthr.apple.com','tthr.apple.com.invalid'))['ready']
 assert not restricted_dns_status(txt.replace('100.78.140.101','1.1.1.1',1))['ready']
\n\ndef test_dns_status_extra_domains_preserved_and_no_order_assumption():
 from split_routes import restricted_dns_status,DNS_DOMAINS
 txt='  - ts.net. -> 199.247.155.53\\n'+'\\n'.join('  - '+d+'. -> 100.78.140.101' for d in reversed(DNS_DOMAINS))
 assert restricted_dns_status(txt)['ready']
''';p.write_text(s)
p=R/'dashboard.html';s=p.read_text()
s=s.replace('這項管理端變更尚待完成。','這四個 restricted DNS 規則已完成新增，保留原有其他 DNS 設定；即時同步狀態見上方。')
s=s.replace('到 Tailscale 管理頁的 Machines → Pi5 → Edit route settings 核准後，系統會分流這些目的地並對已加入名單的裝置拒絕 UDP/443，促成天氣 TCP 回退。','四條路由已核准並同步至受測 Mac；對已加入中轉名單的裝置，UDP/443 會快速拒絕以促成 TCP 回退。')
s=s.replace('完整 relay 分流驗收須以路由核准及新請求為準。','本輪已驗證核准後的 relay 路由、實際封包與 Mac 原生請求。')
s=s.replace('Mac 於 Exit Node 關閉、系統代理關閉時已有原生中轉連線證據；','Mac 於 Exit Node 關閉、系統代理關閉時已有原生中轉連線證據；')
s=s.replace('Relay 子網路已核准；裝置仍須啟用子網路路由並正確使用 AdGuard DNS。','Relay 子網路已核准；裝置 Exit Node 保持 None／無。')
needle="const split=s.splitRoutes||{};"
s=s.replace(needle,needle,1)
needle="$('networkState').textContent=split.relayRoutingReady?"
s=s.replace(needle,"$('networkState').textContent=split.configurationReady?",1)
# Add distinct actual route and egress status without overstating IPv6 forwarding.
needle='<p>共用這些目的 IP 的其他 Apple 連線也可能經過 Pi5；'
s=s.replace(needle,'<p><strong>IPv6 出口狀態：</strong>Pi5 目前缺少對外 IPv6 路由，已加入早期 QUIC 拒絕及有條件 TCP 快速重設，讓已加入名單的裝置回退 IPv4；Pi5 恢復目的地 IPv6 路由時，TCP 保護規則會自動停止匹配。</p>'+needle,1)
p.write_text(s)
p=R/'README.md';s=p.read_text().replace('傳輸層 1.0.0','傳輸層 1.0.1')
s=s.replace('跨網路 relay 分流須完成下列控制端設定再驗收。','四條 relay 路由已核准、同步至受測 Mac，並完成目的地路由與回退驗證；其他實際網路環境及 iOS 真機仍須獨立驗證。')
s=s.replace('管理端需在 Machines → Pi5 → Edit route settings 核准：','本輪已在控制端核准，Mac 已收到以下路由：')
s=s.replace('此管理端設定尚需以現場管理頁狀態確認。','四個 restricted DNS 已由管理頁新增，並從 Pi5 與 Mac 的 Tailscale DNS 設定重新核對。')
s=s.replace('`network_rules.py` 只拒絕已加入名單裝置、指定目的地的 UDP/443；TCP、DNS、Tailscale 隧道本身及其他目的地不受此拒絕規則影響。','`network_rules.py` 對已加入名單裝置、指定目的地的 UDP/443 快速拒絕。額外的 IPv6 relay TCP/443 規則只在 FIB 缺少目的地路由時送出 TCP reset，避免無 IPv6 出口時等待逾時；IPv4 TCP、DNS、Tailscale 隧道本身及其他目的地維持原規則。')
s=s.replace('轉送鏈的 relay 規則則待子網路路由被核准後生效。','relay 路由已核准，IPv4 回退規則於 forward 生效；IPv6 早期規則於 prerouting 生效。')
s+='\n## 核准後驗收\n\n傳輸層 1.0.1 已補上 IPv6 缺出口的快速回退。配置就緒與實際裝置驗收分開記錄，詳見 `reports/approved-split-final.json`。早期錯誤探測與修正後結果均保留於 `research/approved-split/`；資料翻譯層仍為 0.3.1，既有 AQI 自訂量尺問題維持獨立待處理狀態。\n';p.write_text(s)
print('status and documentation updated')
