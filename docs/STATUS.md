# Current project status

Last updated: 2026-09-30 (Asia/Taipei)

## Purpose and operating boundary

The project preserves the native Apple Weather UI while using CWA data for supported Taiwan weather fields. The Pi 5 performs the live translation. Opted-in devices reach it through Tailscale and AdGuard Home and must trust a CA constrained to `weatherkit.apple.com`.

This repository is the maintained public source checkout. It is not a pending handoff package, and a commit here is not automatically deployed. Production state must be verified directly on the Pi 5 before any operational change.

## Deployed state

| Area | Current state |
|---|---|
| Translation | Version 0.3.2 is deployed |
| Transport | Version 1.0.2 is deployed |
| Source revision | Review `1b4c958` is published; later AQI loading repair `662eed9` is published and deployed on the Pi 5 |
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

The later AQI loading repair serves the missing native Taiwan scale locally. The confirmed 404 retry wait took 4.27-4.31 seconds and delayed all weather products. After repair, Mac Weather plus scale requests took 0.291-0.539 seconds; a subsequent process launch reached first data propagation 0.548 seconds after launch dispatch. AQI cards render and a fresh Chiayi response's AQI/category/scale match its source. The first fixed launch including initial scale acquisition reached first propagation after 1.086 seconds from dispatch. The user subsequently confirmed iPhone loading within one second. Four iOS weather requests and two scale requests returned HTTP 200; two final transformed responses decoded to source-matching AQI 77 and 75 with matching pollutant units/amounts. The iPhone duration is user-confirmed; no instrumented launch duration was recorded. These are dated data-readiness samples, not a universal or frame-accurate launch guarantee. See [loading evidence](evidence/latency-aqi-20260930.json).

The Pi 5 returns valid cache entries without waiting for a refresh lock and checks active datasets every 30 seconds, refreshing them within 60 seconds of expiry. Dataset TTLs, stale limits, retry behavior, and four-download concurrency are unchanged. Full Apple responses are not cached.

Before optimization, 55 native translations had a 284 ms median and 1,295 ms p95. Initial post-deployment Mac requests had proxy totals of 308, 156, and 140 ms, but the samples are not matched and do not establish a percentage speedup. See [Performance](PERFORMANCE.md).

## Deployed performance and logic fixes - 2026-09-30

The reviewed source (`1b4c958`) is published on GitHub `main` and deployed on the Pi 5. Before installation, all affected live files matched the checkout baseline. A scoped backup preserves the prior files and service state; all 27 installed source/test hashes match the reviewed commit, and 17 protected environment, certificate, enrollment, and configuration files retain their contents and modes.

- Codec work now indexes forecast points, sorts pressure points once, reuses getter/schema layouts, combines AQI/warning root rebuilds, and avoids two HTTP buffer copies. Float32 writes compare stored values; warning rebuilds verify final content.
- The existing four-entry grid cache now retains recently used entries. Unchanged GRIB subsets are validated without rewriting or rehashing them; independent fields survive a sibling download failure, and Range reads stop at their size limit.
- Conflicting forecasts/WRF accumulations, invalid visibility/grid metadata, null wind direction, county-specific warning hazards, and missing humidity in pressure derivation are guarded.
- SNI parsing handles fragmented headers and rejects invalid declared boundaries. Proof writes use one disk worker within the translation deadline, first ntfy notifications work during early uptime, and failed enrollment configuration restores AdGuard and managed metadata.
- Proof artifacts are encoded candidates. Final bridge events identify the served outcome; `/status` shows a proof only for a modified response.

Mac verification passed 130 Python tests (128 integration tests plus two API tests after the final integration fix) and 40 Node tests. Loopback codec HTTP smoke and a replay of real cached GRIB precipitation/pressure both passed. Local codec batch means improved by about 53-60%; each unchanged full worker run avoids rewriting about 56.1 MB of existing subsets. These are work/latency measurements, not measured power or temperature reductions. See [review evidence](evidence/code-review-20260930.json).

Pi 5 verification passed all 130 Python and 40 Node tests. API, codec, reverse proxy, forward proxy, and SNI services are running; API/codec health returned HTTP 200. A real model-worker run completed successfully with 12 precipitation and 12 pressure records, no errors, and zero download bytes. An isolated deployed-bridge timeout returned the unchanged compressed Apple bytes and headers after 3.5051 seconds.

A fresh native Mac Taichung preview displayed 29°C, derived high/low 35°C/26°C, humidity 78%, and dew point 24°C. Its final `modified` event matches the candidate proof: all 540 reported changes match final decoded getters, and 286 current/hourly source assignments match the snapshot. Translation took 491 ms. This single sample does not establish an end-to-end speedup. See [deployment evidence](evidence/deployment-20260930.json).

## Validation summary

- Mac and Pi 5 each passed 89 Python and 37 Node tests for version 0.3.2.
- Twenty retained native payloads passed the final consistency replay.
- A fresh native Mac city preview loaded under 0.3.2 and displayed the validated current temperature and derived extrema.
- Earlier native iPhone evidence includes two Weather responses and one Widget response with 2,160 mapped fields verified.
- The Watch recovery is supported by the user's device confirmation and subsequent successful `nanoweatherd_watchOS` transformations.
- New physical iPhone and Watch UI acceptance specifically for 0.3.2 has not been performed. Do not infer it from server tests.
- The 2026-09-30 review has fresh Pi and native Mac acceptance; new physical iPhone/Watch acceptance and power/temperature measurements remain separate.

## Current acceptance boundary

The `TAIWAN_AQI` descriptor is now served locally for `zh-Hant-TW` and `en-US`; the Mac displays the AQI value, category, and gradient. The user explicitly confirmed iPhone loading within one second, and its served AQI payloads match official LinkedAPI observations. Instrumented iPhone timing, physical iPhone/Watch AQI-card rendering, advanced AQI details, unsupported locales, and every network condition still need separate evidence.

Other limitations are documented in [Known issues](KNOWN_ISSUES.md). Historical reports in `docs/history/` retain the facts and limitations of their dates; statements that routes, iPhone enrollment, or Watch trust were pending are superseded by this status.

## Evidence map

- `docs/evidence/accuracy-032.json`: current mapping-policy acceptance.
- `docs/evidence/latency-20260920.json`: cache and latency deployment evidence.
- `docs/evidence/watch-diagnostics-20260920.json`: Watch investigation and recovery evidence.
- `docs/evidence/production-source-manifest.json`: hashes of the initial production source extraction.
- `docs/evidence/repo-verification.json`: repository verification at the recorded date.
- `docs/evidence/code-review-20260930.json`: local performance/logic review, regressions, microbenchmark, and dated claim boundaries.
- `docs/evidence/deployment-20260930.json`: published/deployed source, Pi tests, protected-file checks, service/model health, fallback, and correlated native Mac acceptance.
- `docs/evidence/latency-aqi-20260930.json`: missing-scale root cause, separate repair deployment, Mac loading measurements and rendered AQI/source correlation.
- `infra/snapshots/`: dated service, routing, DNS, and dependency snapshots.
- `.private/`: excluded raw captures, precise location evidence, and private runtime material.
