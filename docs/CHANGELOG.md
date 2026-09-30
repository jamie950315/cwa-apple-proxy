# Changelog

## Native AQI loading repair deployed - 2026-09-30

Confirmed that native Weather waits for the missing `TAIWAN_AQI` descriptor: Apple 404 retries added about four seconds before weather data was published. Added a local native JSON descriptor for Taiwan's official six categories in `zh-Hant-TW` and `en-US`; AQI values and source attribution remain unchanged.

Locally committed source `662eed9` is deployed with a four-file rollback manifest. Mac and Pi each passed 44 affected Python tests; only reverse and forward proxies restarted. All 17 protected files retain their contents/modes. Native Mac AQI cards rendered 77/Moderate and 47/Good; the fresh city's decoded AQI/category/scale match its CWA source and final event.

Mac weather-plus-scale requests took 0.291-0.539 seconds, and a subsequent process launch reached first data propagation 0.548 seconds after dispatch. Initial scale acquisition plus app startup took 1.086 seconds; this is not a blanket sub-second guarantee. The user subsequently reported fast, normal iPhone loading. Fresh iOS weather/scale requests returned HTTP 200, and two final served AQI/pollutant payloads match official LinkedAPI observations. Precise iPhone launch timing and physical iPhone/Watch AQI-card acceptance remain separate. This repair has not been published to GitHub. See [loading evidence](evidence/latency-aqi-20260930.json).

## Performance and logic review deployed - 2026-09-30

Published source commit `1b4c958` on GitHub `main` and installed 27 reviewed source/test files on the Pi 5 after baseline verification and a scoped backup. All installed hashes match; 17 protected environment, certificate, enrollment, and configuration files retain their contents and modes.

Pi verification passed 130 Python and 40 Node tests. Restarted the five affected services; API/codec health is HTTP 200. The real model worker completed with 12 APCP and 12 pressure records, no errors, and zero download bytes. Isolated deployed-bridge fallback preserved compressed Apple bytes and headers after 3.5051 seconds.

Fresh native Mac Taichung acceptance rendered 29°C and derived high/low 35°C/26°C. The correlated final response passed 540 getter-change checks and 286 current/hourly source checks. The existing native AQI-scale 404 remains; no new physical iPhone/Watch acceptance or power/temperature measurement was performed. Translation/transport compatibility versions remain 0.3.2/1.0.2. See [deployment evidence](evidence/deployment-20260930.json).

## Local performance and logic review - 2026-09-30

Reviewed runtime modules and fixed confirmed source/transport/operational defects. Removed redundant codec scans, sorts, schema introspection, root rebuilds and buffer copies; restored the existing grid cache's LRU behavior; skipped writes/hashes for unchanged GRIB subsets.

Guarded conflicting forecast/model values, malformed grid/visibility inputs, null wind direction, missing humidity in pressure derivation, county-specific warning hazards and warning compilation/content verification. Made retry-backoff stale limits consistent, allowed environment-only CWA keys, retained independent worker fields after a sibling failure, and bounded Range-body consumption.

Fixed fragmented ClientHello handling and declared-message bounds, proof writes outside the deadline, first-notification suppression during early uptime, and incomplete AdGuard/enrollment rollback. Candidate proof artifacts now correlate with final serving events; status diagnostics exclude proofs for fallback responses.

Verification at the review milestone: 130 Python and 40 Node tests, loopback HTTP codec flow, real cached GRIB replay, repository checks, and controlled local benchmarks. Deployment/publication followed in the separate milestone above; no measured power/temperature reduction. See [review evidence](evidence/code-review-20260930.json).

## Documentation refresh - 2026-09-20

Converted maintained repository documentation to English, replaced the handoff-oriented entry point with a current status document, updated public-repository and GitHub state, and removed stale pending language from README and agent instructions. Historical evidence remains dated and does not override current status.

## 0.3.2 - 2026-09-20: aligned-source accuracy and coverage

Deployed coherent same-station thermodynamics, exact hourly forecast points and PoP windows, validated station `DailyExtreme` data, and derived calendar-day extrema with synchronized occurrence times.

Rainfall now requires complete source windows and compatible phase companions. Retained Apple rain phase is reported as mixed-source. Fractional rainfall allocation, hazard-based PoP disaggregation, fabricated trace amounts, and the grid-only temperature override were removed. Reports now include source assignments even when values are unchanged, source-kind counts, and retention reasons.

Mac and Pi 5 each passed 89 Python and 37 Node tests. Twenty native replays passed checked invariants, and a fresh Mac native preview loaded 0.3.2 successfully. Cache behavior, transport, CA, and fallback remained unchanged. No calibrated disaggregation or extended WRF horizon was deployed.

## Research and audits - 2026-09-20

### Accuracy and coverage research

Measured exact-source compatibility by forecast horizon, found unused station daily-extreme values/timestamps, and reviewed official precipitation products and temporal limits. The resulting exact/coherent policy was subsequently implemented in 0.3.2.

### Temperature and precipitation correctness audit

A read-only audit verified 1,975 encoded scalar writes in 20 native proofs but rejected the 0.3.1 mapping semantics: extrema used shifted windows and Apple timestamps, PoP was uncalibrated, and precipitation companions could become inconsistent. This evidence motivated the 0.3.2 policy.

### Cache latency optimization and source audit

Deployed proactive refresh of existing dataset caches and immediate valid-cache reads during refresh. TTL, stale limits, concurrency, and the translation deadline remained unchanged. Removed an unused warning-summary request, verified identical normalized output, and added per-stage timing.

### Apple Watch diagnostics and recovery

Added privacy-limited TLS/HTTP transport diagnostics without changing routing, DNS, CA, enrollment, or weather mapping. The user then installed the CA on Apple Watch and confirmed recovery with Tailscale enabled; later server logs contained successful watchOS transformations.

## 2026-09-11: repository initialization

Extracted the complete deployed Pi 5 source, vendor files, tests, and systemd/Serve/DNS/nftables snapshots into the Mac Git checkout. Added repository instructions, operations documentation, source-field tables, decisions, limitations, evidence manifests, bootstrap/testing tools, and secret scanning.

Captured the full production dependency freeze and added missing GRIB/spatial dependencies. Kept the Pi 5 program, DNS, and services unchanged during repository construction. The user excluded the unhealthy `jarvis` host.

## Transport 1.0.2

Enabled **Use with exit node** for four restricted DNS entries. Verified fresh Mac Weather responses with None, Pi 5, A1-JP, A1-US, and two representative Mullvad exits. Twelve payloads and 10,846 mapped fields passed decoding checks; the Mac configuration was restored afterward.

## iPhone enrollment

After the user installed and trusted the CA, enrolled `100.123.14.68` for IPv4/IPv6 interception. Two native Weather responses and one Widget response produced 2,160 verified mapped fields.

## Transport 1.0.1

After approval of four relay routes, added four restricted DNS entries. Added early QUIC and missing-FIB IPv6 TCP fallback for the Pi 5 environment without a public IPv6 route.

## Transport 1.0.0

Moved from a full-tunnel Pi 5 exit requirement to restricted DNS plus relay-specific routes. Explicitly separated route advertisement from control-plane approval.

## Data 0.3.1

Added rain stations, official temperature analysis, one-hour radar QPF, WRF cumulative-precipitation differences, PoP derivation, pressure/visibility/fresh gusts, astronomy, LinkedAPI AQI, warnings, and the 3.5-second asynchronous fallback notification. Later semantic audit findings were corrected or guarded by 0.3.2.

## Data 0.2.0 and protocol research

Captured the native WeatherKit `api/v2` / `WK2.Weather` FlatBuffers protocol and built the CA/SNI/Serve/AdGuard/Tailscale path. Implemented the initial current-temperature and township-forecast overrides while preserving unknown native payload data.
