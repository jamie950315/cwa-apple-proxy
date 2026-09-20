# Known issues and future work

## P1: native Taiwan AQI scale

CWA LinkedAPI delivers Taiwan MOENV AQI data, and the mapper writes `scale=TAIWAN_AQI`. The native app then requests `/api/v1/airQualityScale/zh-Hant-TW/TAIWAN_AQI`, which currently returns 404. Successful root/scalar decoding proves the payload value but not complete AQI-card rendering.

A correct fix requires capturing a supported scale response, understanding the private classification/color/range schema, implementing the Taiwan scale endpoint, adding mapping tests, and validating the native Mac and iPhone UI. Relabeling Taiwan values as another country's scale is not acceptable.

## Mapping limits after 0.3.2

The semantic defects identified in the 0.3.1 temperature/precipitation audit are corrected or guarded in 0.3.2. Historical failure evidence remains in `evidence/correctness-20260920.json`; current acceptance is in `evidence/accuracy-032.json`.

- Calendar-day extrema are derived from validated observations and complete hourly samples. They are not exact continuous-time official extrema.
- Incompatible rain phases, multiple ByType entries, snow fields, partial windows, and conflicting values retain Apple.
- Unmatched hourly/daily PoP remains Apple. The former uncalibrated 3-hour/12-hour disaggregation is disabled.
- Trace rain is nonnumeric. Rainfall is not fractionally split or blended across radar/model families.
- Current thermodynamics use one station/time. Temperature-analysis grids are diagnostics only.
- Coverage intentionally decreases where source semantics do not align.
- Apple summaries, comparisons, icons, and other unmapped fields may disagree with CWA values.
- No calibrated disaggregation model or validated WRF +78/+84-hour extension is deployed.

## Geographic and forecast representativeness

Nearest representative township points and horizontal station distance are imperfect near administrative borders and in mountainous terrain. Future improvement may use administrative polygons, elevation, and terrain-aware selection. Any new derived forecast needs independent forecast-skill validation; conservation or schema tests alone are insufficient.

## Operations

- WRF APCP and pressure extraction rely on the validated current file layout. A dynamic GRIB message index would be more robust; existing fail-closed checks must remain.
- Leaf-certificate and CA renewal are manual.
- Pi 5, Tailscale, TLS, or Apple-upstream outages occur before translation fallback and need separate monitoring.
- New OS releases and unknown FlatBuffers slots require renewed capture and compatibility testing.
- `configurationReady` covers current route/DNS conditions, but the exit-DNS flag is a recorded snapshot rather than continuously queried live state.
- Linux units, host addresses, and some paths are deployment-specific and are not yet parameterized for a second host.
- Physical iPhone/Watch UI acceptance specifically for 0.3.2 remains separate from server replay and Mac UI evidence.

## Resolved Watch issue

The user installed the custom CA on Apple Watch and confirmed Weather recovery with iPhone Tailscale enabled. Four subsequent watchOS transformations support the diagnosis. No routing workaround was necessary. A CA installed only on the iPhone is not sufficient Watch acceptance; do not reset, unpair, or introduce MDM automatically.

## Validation still requiring separate evidence

Treat each of these as an independent test: iPhone under each exit node, Wi-Fi/cellular roaming, native AQI and other new cards, full-device restart and disconnect recovery, long-running reliability, and actual delivery of ntfy notifications to a subscribed device.

## Out of scope

The user explicitly excluded the unhealthy `jarvis` host. Preserve existing failure evidence, but do not treat that host as a project blocker or resume repair without a new request.

Historical reports may describe routes, iPhone enrollment, or Watch trust as pending. Those statements are dated and superseded by [Current status](STATUS.md).
