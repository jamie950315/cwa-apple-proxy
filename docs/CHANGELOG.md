# Changelog

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
