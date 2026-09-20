# CWA Weather Bridge transport 1.0.0: no-exit-node deployment

Verified: 2026-09-11T15:03:07+08:00. Translation 0.3.1; transport 1.0.0.

> Historical evidence. Route approval, restricted DNS, iPhone enrollment, and exit-node coexistence were completed by later versions.

The Pi 5 deployed direct WeatherKit DNS, scoped UDP/443 rejection, enrolled-client rules, and route-status reporting. With Mac exit node set to None, native Weather and Widget produced fresh transformed responses while ordinary internet traffic continued through the original Wi-Fi route.

At this stage four relay routes were advertised but still awaiting control-plane approval. The successful Mac test therefore proved the direct DNS path, not the full cross-network relay path.

| Check | Result |
|---|---|
| Python / JavaScript tests | 68 / 23 passed |
| Mac exit node | None before and after |
| Fresh native responses | Four Weather and one Widget |
| Mapped fields | 932 or 961 per Weather response; 356 for Widget; zero skipped eligible writes |
| Pi 5 UDP/443 rejection | IPv4 94 ms; IPv6 97 ms |
| Apple, Google, Pi 5 HTTPS, CWA health | HTTP 200 |
| Relay routes | Advertised; approval pending at this version |

The planned relay prefixes were `17.253.0.0/16`, `2403:300:a00::/40`, `2620:149:a00::/40`, and `2a01:b740:a00::/40`. The existing LAN and exit-node advertisements remained unchanged.

Rollback used `split_routes.py withdraw` for project-managed prefixes and `bridgectl.py disable <Tailscale-IP>` for one client. Translation behavior and the 3.5-second fallback were unchanged.

Evidence: `research/no-exit/activation.json`, `mac-acceptance.json`, `final-network-evidence.json`, `final-tests.log`, and `data/split-route-status.json`.
