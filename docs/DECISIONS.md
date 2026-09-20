# Architecture decisions

| Decision | Rationale and boundary |
|---|---|
| Native Apple Weather UI with Pi 5 translation | Preserves the preferred interface and reuses the existing self-hosted Tailscale/AdGuard environment |
| Captured `WK2.Weather` FlatBuffers as the wire contract | Native clients differ from public WeatherKit REST; implementation follows observed payloads |
| CWA-first field-level hybrid | Preserves Apple-only fields and CWA coverage gaps while recording field provenance |
| In-place scalar writes plus omitted-scalar expansion | Minimizes disturbance to unknown payloads; rebuilt AQI/warning roots are decoded after writing |
| Exact/coherent source groups in 0.3.2 | Accuracy takes precedence over overwrite count; incomplete or incompatible groups retain Apple |
| 3.5-second budget with original body/header fallback | Limits added latency and keeps an already-obtained Apple response usable; ntfy is asynchronous |
| Background WRF Range subsets | Avoids downloading an approximately 180 MB model file per app request; validates ETag, range, and GRIB semantics |
| Name-constrained CA and client opt-in | Limits interception to WeatherKit and avoids routing clients that do not trust the CA |
| Restricted DNS, relay-specific routes, and scoped QUIC rejection | Native clients race relay and QUIC paths; DNS or PAC alone did not cover the observed traffic |
| Optional exit node | Transport 1.0.2 allows WeatherKit split routing while retaining the selected normal exit |
| IPv6 missing-FIB fast fallback | Early UDP rejection and a TCP reset only when the destination route is missing allow IPv4 to proceed |
| Exclude `jarvis` | The user identified that host as unhealthy and removed it from project acceptance |
| Public source repository with private evidence excluded | Makes maintained code and documentation accessible without publishing credentials, raw locations, or private captures |

## Approaches not used by default

A macOS PAC or system HTTPS proxy did not cover the native relay path by itself and remains disabled. Using the Pi 5 as a full-tunnel exit node was useful for early validation but is no longer required for WeatherKit routing. When the private npm package was unavailable, the codec was extracted from a public NSRingo release bundle with its license and NOTICE retained.

Operational success is judged by real HTTPS and transformed-payload evidence, not by a certificate-store command alone. Permission failures are handled through already authorized tools and SSH, not by expanding host privileges.
