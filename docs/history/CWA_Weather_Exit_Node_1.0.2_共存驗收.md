# CWA Weather Bridge transport 1.0.2: exit-node coexistence acceptance

Verified: 2026-09-11T17:21:37.649673+08:00. Translation 0.3.1; transport/DNS 1.0.2.

The four restricted DNS entries retained nameserver `100.78.140.101` and enabled **Use with exit node**. Existing global DNS, split DNS, LAN/relay advertisements, CA, firewall rules, and weather translation remained unchanged.

| Exit node | Public egress | Weather path | Fresh native responses | Result |
|---|---|---|---:|---|
| None | Taiwan | Pi 5 | 2 | Passed |
| Pi 5 | Taiwan | Pi 5 | 1 | Passed |
| A1-JP | Japan | Pi 5 | 1 | Passed |
| A1-US | United States | Pi 5 | 3 | Passed |
| `jarvis` | Unavailable | Pi 5 reachable | 0 | Public internet timed out |
| `jp-tyo-wg-001` | Japan | Pi 5 | 3 | Passed |
| `us-lax-wg-402` | United States | Pi 5 | 2 | Passed |

Twelve retained native Weather responses passed 10,846 decoded field comparisons. Python 76 and JavaScript 23 tests passed. The Mac was restored with empty `ExitNodeID` and `ExitNodeIP`; DNS, route acceptance, LAN access, and normal Wi-Fi routing matched the pre-test state.

Some 40-second same-city observation windows produced no new response because of native caching. Follow-up searches for new cities generated fresh traffic; the original empty observations remained recorded. Initial isolated UDP probe timeouts were followed by three successful spaced probes and were not treated as proof of loss-free networking.

The iPhone already had independent native Weather/Widget evidence, but this exit-node matrix used the Mac only. The 3.5-second translation fallback and AQI-scale 404 were unchanged.

Evidence: `research/exit-compatible/mac-matrix.json`, `mac-*.fresh.json`, `mac-final-restore.json`, `native-audit.json`, `reports/exit-compatible-native/`, and `config/exit-dns-compatibility.json`.
