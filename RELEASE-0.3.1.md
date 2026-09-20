# CWA Weather Bridge 0.3.1 research and deployment record

Generated: 2026-09-11T12:06:12.121239+08:00

> Historical release record. Translation version 0.3.2 is current. The interpolation and precipitation-disaggregation behavior described here was later corrected or guarded; see `docs/STATUS.md`.

## Machine acceptance

Production API and codec reported version 0.3.1. All 368 township queries passed. A 1,000/1,000 local FlatBuffers replay passed with 89.27 ms median and 183.34 ms p95. Replay evidence was separate from native-device and UI validation.

The release added station observations, temperature analysis, observed rain, one-hour radar QPF, WRF precipitation, township forecasts, pressure, visibility, warnings, astronomy, and Taiwan MOENV AQI through CWA LinkedAPI. It preserved unsupported Apple fields and unknown protocol slots.

The CWA fetch and translation path had a shared 3.5-second deadline after an Apple response was obtained. On timeout or translation failure it preserved the original Apple body and headers and sent an asynchronous ntfy notification with 300-second deduplication. An isolated test fell back after 3.5045 seconds and received HTTP 200 from ntfy; that receipt did not prove device notification display.

The 0.3.1 release used uncalibrated temporal interpolation and probability/rainfall disaggregation. Those semantics are historical and must not be restored. Version 0.3.2 uses exact/coherent source groups instead.

Official interfaces:

- CWA OpenAPI: <https://opendata.cwa.gov.tw/apidoc/v1>
- CWA REST: `https://opendata.cwa.gov.tw/api/v1/rest/datastore/<dataset>`
- CWA File API: `https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/<dataset>`
- CWA LinkedAPI: `https://opendata.cwa.gov.tw/linked/graphql`
- Native response MIME: `application/vnd.apple.flatbuffer;messageType=WK2.Weather`
