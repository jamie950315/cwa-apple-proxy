# Latency and cache behavior

## Performance review and deployment - 2026-09-30

The reviewed source (`1b4c958`) is published and deployed. Controlled Mac workload evidence is recorded in [review evidence](evidence/code-review-20260930.json); Pi tests, runtime health, and native Mac acceptance are recorded separately in [deployment evidence](evidence/deployment-20260930.json).

| Controlled workload | Before | After | Measurement |
|---|---:|---:|---|
| Codec scalar mapping, 274 hourly samples | 2.069 ms | 0.963 ms | Median of nine batch means, 100 transforms per batch |
| Codec mapping plus AQI/warning rebuild | 2.578 ms | 1.027 ms | Same fixture, warmup, and batches |
| Frequently reused temperature grid among four QPF updates | 2 parses / 200,000 cells | 1 parse / 100,000 cells | Existing four-entry cache; QPF parses unchanged |
| Unchanged full GRIB-subset cache | 24 binary rewrites / 56,116,848 bytes | 0 binary rewrites | Pi inventory plus controlled unchanged-ETag regression |

The codec uses one forecast time index and one sorted pressure series per response, caches fixed getter/schema layouts, combines root rebuilds, and avoids redundant input/output binary copies. Float32 values are rounded before comparison so an already-matching payload reports no scalar modifications. Validated source assignments still count.

The grid cache keeps its existing four-entry capacity and updates recency on a hit. The worker retains GRIB decoding, parameter/time checks, and the existing +72-hour horizon; unchanged subsets skip only redundant disk writes and hashes. A replay using real cached +6-hour APCP and pressure messages validated all 368 township values with one mocked HEAD, no GET, and no subset rewrite. That replay took 38.758 seconds on the Mac, including ecCodes grid lookup; it is not a worker speedup measurement.

Proof file work runs off the event loop with at most one in-flight worker per bridge. Waiting uses the existing translation deadline. A worker finishing after fallback records an encoded candidate; final serving status comes from the bridge event. `/status` exposes proof changes only for a modified response.

The codec benchmark uses a 40,844-byte retained native fixture, 50 warmup calls, Node v23.11.0, and the same synthetic snapshot before/after. Raw batch results and fixture/module hashes are in the review evidence. Local reductions of approximately 53% and 60% cannot be converted into Pi power, temperature, end-to-end speed, or device UI claims. Dataset TTLs, stale-data policy, refresh schedule, download concurrency, and the 3.5-second deadline are preserved.

The actual post-deployment Pi model run generated 12 APCP and 12 pressure records with no errors and zero download bytes. A native Mac Taichung response took 491 ms for translation (420 ms CWA, 65 ms codec, 5 ms proof); its 540 reported changes matched final getters. This request was not matched against a pre-deployment request and does not establish a percentage speedup or power/temperature reduction.

## 2026-09-20 optimization

Pi5 already caches raw CWA datasets in memory and on disk. The avoidable wait was on cache expiry: requests could wait for a dataset download and for the per-dataset refresh lock. The old warmup ran every 300 seconds, after the shortest TTL had elapsed, and did not refresh recently used county forecasts.

The deployed changes are:

- Check warmup every 30 seconds and refresh active cached datasets within 60 seconds of expiry. The fixed core datasets remain warm; county forecasts are eligible for six hours after use.
- Return a still-valid cache entry before taking the dataset lock. A background download cannot block an otherwise valid hit.
- Retain original TTLs, source-time validity checks, four-download concurrency, retry backoff, stale limits, and the 3.5-second translation deadline. An expired entry still follows the original foreground behavior.
- Remove the unused W-C0033-001 alert summary from snapshot and warmup. W-C0033-002 detail still supplies warnings. Frozen-time replay against Pi5 disk data produced exactly the same snapshot with 11 rather than 12 source calls.
- Record `appleResponseMs`, `cwaMs`, `codecMs`, `proofMs`, and `proxyTotalMs` in the existing bridge log. These durations do not include the device's DNS, Bluetooth, UI scheduling, or rendering time. `appleResponseMs` spans incoming request completion to upstream response completion; it is not a pure Apple compute-time measurement.

No entire Apple response is cached or reused across clients. The native response can vary by location, requested datasets, platform, and authentication context. The optimization also does not extend the lifetime of CWA data to make the UI appear faster. Early refresh slightly increases CWA request frequency (a 300-second dataset can refresh about every 240–270 seconds).

## Cache inventory

| Source | Existing TTL | Storage |
|---|---:|---|
| Station observations, rain gauges, radar QPF, warning detail | 300 seconds | Pi5 memory and atomic JSON disk cache |
| AQI via CWA LinkedAPI | 600 seconds | Pi5 memory and disk |
| County forecasts and temperature analysis | 1,800 seconds | Pi5 memory and disk |
| Sun/moon tables | 43,200 seconds | Pi5 memory and disk |
| WRF precipitation/pressure | Existing hourly worker | Validated local model file, memory refreshed by file mtime |

The first request for an uncached county, an extended outage, and Apple/network delays may still be slow. No stale-data guarantee was expanded.

## Evidence and limits

- Before deployment, 55 native responses in 24 hours had median translation time 284 ms, p95 1,295 ms, maximum 1,486 ms. These measurements excluded Apple response time. Historical spikes cannot retrospectively be assigned to an individual stage.
- By client: Watch median 78.5 ms (4 responses); iPhone Weather median 106 ms (3); iPhone Widget median 148 ms (13); Mac Widget median 299 ms (35). Payload shapes differ; these are not equivalent workloads.
- Warm Pi5 API median: 34.70 ms; codec median: 14.31 ms (8 local requests each). A local replay of a small native payload took approximately 52–54 ms after warmup, with proof writes around 1.7 ms.
- Controlled synthetic 200 ms fetch: foreground expiry wait was 200.588 ms before, 0.007 ms after prefetch. Both fetched once and retained a 300-second TTL. This demonstrates moving work off the foreground path, **not** an end-to-end App speedup factor.
- Initial post-deployment native Mac requests: proxy totals 308, 156, and 140 ms; Apple stages 88, 78, and 59 ms; CWA stages 172, 36, and 51 ms; codec stages 42, 37, and 25 ms. Mac Weather visibly loaded real values. There is no matched pre-deployment end-to-end sample, so no percentage speedup is claimed.
- Mac and Pi5 each passed 81 Python and 23 Node tests. The raw dataset format and weather mapping semantics are unchanged.
- Live background refresh was observed without expiring or clearing any cache: observation age changed from 237 seconds to 15 seconds across a 20-second interval, implying refresh around age 242 (before the 300-second TTL). Temperature analysis and AQI also refreshed before their TTLs; seven datasets were fetched with no recorded errors.

Rollback source: Pi5 `backups/perf-cache-20260920/` contains the four prior Python modules and the two prior tests. Restore those files and restart only `cwa-weather-api` and `cwa-weather-proxy` after checking active connections. DNS, routing, CA, client enrollment, codec, and data files were not changed.
