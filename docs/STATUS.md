# Current project status

Last updated: 2026-09-20 (Asia/Taipei)

## Purpose and operating boundary

The project preserves the native Apple Weather UI while using CWA data for supported Taiwan weather fields. The Pi 5 performs the live translation. Opted-in devices reach it through Tailscale and AdGuard Home and must trust a CA constrained to `weatherkit.apple.com`.

This repository is the maintained public source checkout. It is not a pending handoff package, and a commit here is not automatically deployed. Production state must be verified directly on the Pi 5 before any operational change.

## Deployed state

| Area | Current state |
|---|---|
| Translation | Version 0.3.2 is deployed |
| Transport | Version 1.0.2 is deployed |
| Runtime | Pi 5 at `/home/jamie/cwa-weather-proxy` |
| Mac | Enrolled; native Weather and Widget transformations have been verified |
| iPhone 14 Pro | Enrolled; native Weather and Widget transformed responses have been verified |
| Apple Watch | CA installed by the user; Weather works with Tailscale enabled; successful watchOS transformations were logged |
| DNS | Four restricted WeatherKit/relay domains point to the Pi 5 and are enabled for exit-node use |
| Routes | Four Apple relay prefixes are advertised and approved |
| Exit nodes | None, Pi 5, and representative third-party exit nodes have worked on the tested Mac |
| Cache | Active CWA datasets refresh before expiry; TTL and stale-data limits remain unchanged |
| Fallback | Translation has a 3.5-second deadline and preserves the original Apple body and headers on failure |
| Out of scope | The unhealthy `jarvis` host is intentionally excluded |

## Accuracy policy in 0.3.2

- Current temperature, humidity, and dew point form one coherent station/time group.
- Hourly temperature-related values use exact same-time CWA points. Missing or inconsistent groups retain Apple values.
- PoP is written only when the CWA interval exactly matches the native interval and duplicate values do not conflict.
- Rainfall uses complete, non-overlapping source windows from a compatible family and initialization. Amounts are not fractionally divided.
- Trace rain remains nonnumeric. Ten-minute accumulation is not presented as instantaneous intensity.
- Compatible rain-only precipitation companions are updated with the amount. A retained Apple rain phase combined with a CWA amount is reported as mixed-source.
- Daily extrema cover local calendar days. Today combines validated observed extrema with remaining exact hourly samples; future days require all 24 hourly points. These extrema are explicitly derived, not official continuous-time extrema.
- Unknown fields and unsupported groups retain the original Apple response.

The final 0.3.2 acceptance replay covered 20 retained native responses with no checked consistency violations and 471/471 exact CWA assignments for the sampled next-24-hour temperature slots. This is correlated payload evidence, not an all-Taiwan forecast-skill guarantee. See [accuracy evidence](evidence/accuracy-032.json).

## Performance and cache state

The Pi 5 returns valid cache entries without waiting for a refresh lock and checks active datasets every 30 seconds, refreshing them within 60 seconds of expiry. Dataset TTLs, stale limits, retry behavior, and four-download concurrency are unchanged. Full Apple responses are not cached.

Before optimization, 55 native translations had a 284 ms median and 1,295 ms p95. Initial post-deployment Mac requests had proxy totals of 308, 156, and 140 ms, but the samples are not matched and do not establish a percentage speedup. See [Performance](PERFORMANCE.md).

## Validation summary

- Mac and Pi 5 each passed 89 Python and 37 Node tests for version 0.3.2.
- Twenty retained native payloads passed the final consistency replay.
- A fresh native Mac city preview loaded under 0.3.2 and displayed the validated current temperature and derived extrema.
- Earlier native iPhone evidence includes two Weather responses and one Widget response with 2,160 mapped fields verified.
- The Watch recovery is supported by the user's device confirmation and subsequent successful `nanoweatherd_watchOS` transformations.
- New physical iPhone and Watch UI acceptance specifically for 0.3.2 has not been performed. Do not infer it from server tests.

## Active limitation

The main confirmed compatibility issue is the `TAIWAN_AQI` scale endpoint. The AQI root can contain Taiwan MOENV values delivered through CWA LinkedAPI, but the native app subsequently requests `/api/v1/airQualityScale/zh-Hant-TW/TAIWAN_AQI`, which currently returns 404. Scalar decoding does not prove complete AQI-card rendering.

Other limitations are documented in [Known issues](KNOWN_ISSUES.md). Historical reports in `docs/history/` retain the facts and limitations of their dates; statements that routes, iPhone enrollment, or Watch trust were pending are superseded by this status.

## Evidence map

- `docs/evidence/accuracy-032.json`: current mapping-policy acceptance.
- `docs/evidence/latency-20260920.json`: cache and latency deployment evidence.
- `docs/evidence/watch-diagnostics-20260920.json`: Watch investigation and recovery evidence.
- `docs/evidence/production-source-manifest.json`: hashes of the initial production source extraction.
- `docs/evidence/repo-verification.json`: repository verification at the recorded date.
- `infra/snapshots/`: dated service, routing, DNS, and dependency snapshots.
- `.private/`: excluded raw captures, precise location evidence, and private runtime material.
