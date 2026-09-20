# Architecture and code map

## Native request

```http
GET /api/v2/weather/zh-Hant-TW/<latitude>/<longitude>?country=TW&timezone=Asia/Taipei&dataSets=...
Host: weatherkit.apple.com
Accept: application/vnd.apple.flatbuffer;messageType=WK2.Weather
```

The implementation targets the private FlatBuffers protocol observed from the native Weather app. Public WeatherKit REST schemas are useful research references but are not the wire contract. macOS, iOS, Watch, and widgets request different dataset combinations and response sizes.

## Live data flow and ports

```text
Device Core Location or searched-city coordinates
  -> Tailscale restricted DNS
  -> per-client AdGuard rule: weatherkit.apple.com A = 100.78.140.101
  -> Pi 5 Tailscale Serve TCP/443
  -> 127.0.0.1:19443 SNI router
       weatherkit.apple.com
         -> 127.0.0.1:18443 mitmproxy reverse proxy
         -> original Apple HTTPS response
         -> 100.78.140.101:18880 /v1/cwa/weather
         -> 127.0.0.1:18881 /transform
         -> field-level rewrite or guarded root rebuild
         -> native client
       other SNI
         -> Pi 5 Tailscale HTTPS :18444
         -> / to 127.0.0.1:8017
         -> /runpod-image-editor to 127.0.0.1:8789

127.0.0.1:18940 is a WeatherKit-restricted explicit forward proxy for tests.
```

Use `infra/live-systemd/` and `infra/snapshots/tailscale-serve.json` to compare installed routing with source units. The SNI router preserves unrelated TLS traffic. Certificate downloads and diagnostics are visible only inside the tailnet; the codec binds to loopback.

## Modules

| File | Responsibility |
|---|---|
| `addon.py` | Request/MIME filtering, 3.5-second budget, CWA and codec calls, original-response fallback, notification, transport timing |
| `api.py` | FastAPI health, diagnostics, normalized weather endpoint, CA/profile downloads, cache warmup |
| `cwa_client.py` | Allowlisted CWA APIs, authentication, four-download concurrency, locks, TTL, bounded stale use, retry backoff |
| `cwa_snapshot.py` | Combines station, township, rain, AQI, grid, NWP, warning, and astronomy data with provenance |
| `cwa_model.py` | Numeric validation, units, dew point, observations, forecasts, daily extrema, geographic distance |
| `cwa_products.py` | Temperature-analysis and one-hour radar-QPF normalization |
| `cwa_nwp.py`, `model_worker.py` | WRF normalization, HTTP Range reads, GRIB2 validation, and cache generation |
| `cwa_alerts.py`, `cwa_astronomy.py`, `cwa_aqi.py` | Warnings, astronomical events, and MOENV AQI delivered through CWA LinkedAPI |
| `mapper.mjs` | Known-field FlatBuffers mapping and guarded AQI/warning root rebuilds |
| `flatbuffer_expand.mjs` | Adds omitted scalar storage while preserving unknown payload regions |
| `weather_math.mjs` | Complete-window rainfall aggregation and NWP pressure interpolation |
| `codec_server.mjs` | Local Node HTTP codec service |
| `vendor/weatherkit-codec.full.mjs` | Codec derived from the NSRingo WeatherKit 3.3.2 bundle; Apache NOTICE retained |
| `sni_router.py` | ClientHello/SNI parsing and bidirectional TLS passthrough |
| `bridgectl.py` | Device opt-in DNS management with backup and failure recovery |
| `split_routes.py`, `network_rules.py` | Route advertisement/status and scoped QUIC/IPv6 fallback rules |

## Runtime constraints

The Apple response is obtained before the 3.5-second CWA/codec deadline begins. Pi 5 outages, Apple upstream failures, and TLS failures are transport failures outside that translation fallback.

Active CWA cache entries refresh shortly before expiry. A valid cache hit does not wait for a concurrent refresh. TTL and stale limits are unchanged, and complete Apple responses are never cached.

Version 0.3.2 writes only exact or explicitly derived compatible groups. Unknown roots and unsupported values remain Apple. Omitted FlatBuffers scalar storage is distinct from a valid zero value and is covered by regression tests. Any root rebuild must be decoded again and compared through final getters, not inferred from intermediate byte offsets.
