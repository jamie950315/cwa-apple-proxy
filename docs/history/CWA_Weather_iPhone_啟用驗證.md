# CWA Weather Bridge: iPhone native-request acceptance

Verified: 2026-09-11 16:22:49 Asia/Taipei. Translation 0.3.1; transport 1.0.1.

The user's iPhone 14 Pro was enrolled for IPv4 and IPv6 interception after certificate installation was confirmed. The proxy received three real native iOS HTTPS requests and produced transformed responses. All three decoded successfully.

User-Agents were `WeatherKit_Weather_iOS_Version 27.0 (Build 24A5430a)` and `WeatherKit_WeatherWidget_iOS_Version 27.0 (Build 24A5430a)`.

| Time | Client | CWA station | Apple temperature | Returned temperature | Mapped scalars | Translation |
|---|---|---|---:|---:|---:|---:|
| 16:18:39 | iOS Widget | National Taiwan University | 27.89 C | 26.6 C | 357 | 152 ms |
| 16:19:18 | iOS Weather | Tainan | 30.02 C | 28.8 C | 889 | 1,383 ms |
| 16:21:00 | iOS Weather | National Taiwan University | 27.84 C | 26.6 C | 914 | 355 ms |

All responses had `skippedFields=0` for eligible writes. A total of 2,160 scalar rewrites were decoded and compared. The Tainan response included 92 hourly points, seven days, and 154 precipitation-related writes.

This proved native HTTPS completion and transformed bytes, not the final rendering of every card. The independent `TAIWAN_AQI` scale endpoint still returned 404. The server could verify routing and DNS but did not directly read the iPhone's current exit-node preference.

Evidence: `reports/iphone-onboarding.json`, `reports/iphone-native-audit.json`, `reports/iphone-native/`, and `research/iphone-onboarding/audit_native.mjs`.
