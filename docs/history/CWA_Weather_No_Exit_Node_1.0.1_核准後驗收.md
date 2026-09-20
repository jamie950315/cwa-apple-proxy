# CWA Weather Bridge transport 1.0.1: approved split-route acceptance

Verified: 2026-09-11T15:50:03.567306+08:00. Translation 0.3.1; transport 1.0.1.

> Historical evidence. iPhone enrollment and exit-node coexistence were completed later.

All four relay prefixes were approved and received by the tested Mac. The Mac kept no exit node and no HTTP/HTTPS/PAC proxy. Ordinary internet traffic used Wi-Fi; Pi 5 and relay-prefix traffic used Tailscale. Four restricted DNS entries were added while existing global and `ts.net` DNS configuration remained intact.

| Check | Result |
|---|---|
| Python / JavaScript tests | 72 + 23 = 95 passed |
| Mac transport checks | 13 passed |
| Fresh native responses | Two Weather; both decoded successfully |
| Apple, Google, Pi 5, Runpod, CWA health | HTTP 200 |
| Relay routes | Four approved; zero pending |
| Restricted DNS | Four pointed to `100.78.140.101` |
| IPv4 relay TCP | Connected |
| IPv6 without a Pi 5 public route | Fast reset allowed IPv4 fallback |

The nftables change handled enrolled relay UDP in prerouting and reset IPv6 TCP/443 only when the destination FIB route was missing. Six final rejection probes completed in 96-101 ms, with a 105 ms IPv6 TCP fallback. One earlier burst timeout remained recorded and was not misreported as zero packet loss.

At this date the iPhone was not yet enrolled. The `TAIWAN_AQI` scale endpoint 404 was an independent issue.

Evidence: `reports/approved-split-final.json`, `research/approved-split/mac-verified-final.json`, `native-audit.json`, and `config-final.json`.
