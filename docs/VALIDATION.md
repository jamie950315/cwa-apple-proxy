# Validation evidence and claim boundaries

| Layer | Existing evidence | What it does not prove |
|---|---|---|
| CWA fetching | Successful observation, township, rain, QPF, WRF, astronomy, warning, and LinkedAPI/AQI fetches | Every field is always present or fresh |
| Version 0.3.2 unit tests | 89 Python and 37 Node tests on both Mac and Pi 5 | Real forecast skill or every native UI state |
| Version 0.3.2 replay | 20 retained native responses, no checked consistency violation, 471/471 sampled next-24-hour temperatures assigned exact CWA points | Independent/all-Taiwan samples or future accuracy |
| Fresh Mac UI | A native city preview loaded 0.3.2 current temperature and derived extrema | iPhone/Watch UI acceptance for 0.3.2 |
| Earlier iPhone native traffic | Two Weather and one Widget response; 2,160 mapped fields decoded and verified | Every card, network, or exit-node combination |
| Apple Watch recovery | User confirmation after Watch CA installation plus four later watchOS transformations | Long-running reliability or every Watch state |
| Transport 1.0.2 | None, Pi 5, A1-JP, A1-US, and two Mullvad exits on Mac; 12 native responses and 10,846 mapped fields | Every exit, iPhone exit switching, or roaming |
| Timeout/ntfy | 3.5045-second fallback preserved compressed Apple body/headers; ntfy returned HTTP 200 | Notification display on the user's subscribed device |
| 2026-09-30 local source review | 130 Python and 40 Node tests; real cached GRIB replay; loopback codec HTTP flow; comparable codec microbenchmark | Deployment, Pi power/temperature changes, or new native UI acceptance |
| 2026-09-30 deployment | All 27 installed hashes match `1b4c958`; 17 protected files unchanged; 130 Python and 40 Node tests on Pi; five services running; real model-worker success | Every future refresh or long-running reliability |
| 2026-09-30 native Mac acceptance | Taichung preview rendered; final event/candidate correlated; 540 final getter changes and 286 current/hourly source assignments verified | Complete AQI card, new physical iPhone/Watch acceptance, or measured energy/temperature reduction |
| 2026-09-30 deployed fallback isolation | Actual 3.5-second budget; 3.5051-second return; compressed original body and all headers preserved | Live outage acceptance or subscribed-device ntfy delivery |

Dated compact evidence is under `docs/evidence/`. Raw native material is excluded in `.private/native-evidence.tar.gz` and retained production report directories.

The latest local source evidence is [code-review-20260930.json](evidence/code-review-20260930.json). The final Python total combines a 128-test integration run and two API regressions added after the serving-outcome integration check; all unaffected evidence was reused. Candidate proof files alone cannot establish delivery; use the final bridge event with the matching `requestId`.

The corresponding deployment evidence is [deployment-20260930.json](evidence/deployment-20260930.json). The Pi ran the complete 130-test Python and 40-test Node suites before the affected services restarted. Native daily vectors can include a preceding day; the accepted high/low values were selected by Taiwan calendar date, not vector index zero.

## Evidence to retain for a new native acceptance run

Record Asia/Taipei time, device/platform User-Agent, exit-node identity, system DNS, routes, service health, original Apple bytes, CWA source and time window, transformed bytes, mapper report, and native UI result. Remove credentials and precise personal location before considering any artifact for Git.

Compare final decoded getter values with both `report.after` and the source snapshot. Define float tolerances. A validated assignment that equals the original value counts as source coverage but not as a byte modification.

Confirm the exit node and network remain constant for the run and restore prior client preferences afterward. Existing cities may hit native caches; use a new supported city when a fresh response is required.

## Repository verification

`scripts/verify_repo.py` checks documentation links, tracked-file policy, source manifests, and likely secrets. `scripts/test.sh` runs the offline program suites. Platform, timestamp, exit code, and test count belong in a dated evidence file when the result is used for a release or deployment claim.

Do not rerun unaffected suites merely to increase the test count. Rerun the narrow affected checks after a documentation-only change, and escalate only when the changed behavior requires it.
