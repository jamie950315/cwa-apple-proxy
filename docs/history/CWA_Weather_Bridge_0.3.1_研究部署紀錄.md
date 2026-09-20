# CWA Weather Bridge 0.3.1 research and deployment record

Verified: 2026-09-11T12:48:23.817091+08:00

> Historical evidence. Translation version 0.3.2 and [current status](../STATUS.md) supersede its mapping policy.

The API and codec reported 0.3.1. Six services and the model-data timer were active and enabled. All 368 township queries passed. A separate 1,000/1,000 FlatBuffers replay had 89.27 ms median and 183.34 ms p95.

A fresh verification passed 52 Python and 23 JavaScript tests. Sixteen retained native macOS Weather/Widget responses decoded successfully. The largest complete app sample verified 952 scalar rewrites, 96 hourly points, seven days, and 201 precipitation-related fields with no omitted-scalar write failures. A native Weather screenshot displayed a 26 CWA temperature.

The release used fresh nearby observations, township forecasts, temperature analysis, rain gauges, radar QPF, WRF, warnings, astronomy, and MOENV AQI through CWA. Unsupported minute precipitation, maps, cloud layers, forecast visibility/gusts, moon phase, proprietary comparison products, unknown fields, and source gaps remained Apple.

The 3.5-second translation fallback preserved the Apple response and used asynchronous ntfy notification. Host, TLS, and network failures before an Apple response were separate transport failures.

Known limits at the time included pending AQI-card/UI acceptance and uncalibrated interpolation/disaggregation. Version 0.3.2 removed or guarded those semantics.

Evidence: `reports/executor-final-audit.log`, `reports/native-031-audit.json`, `reports/executor-closeout-031.json`, and `reports/ntfy-timeout-selftest.json`.
