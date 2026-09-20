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

Dated compact evidence is under `docs/evidence/`. Raw native material is excluded in `.private/native-evidence.tar.gz` and retained production report directories.

## Evidence to retain for a new native acceptance run

Record Asia/Taipei time, device/platform User-Agent, exit-node identity, system DNS, routes, service health, original Apple bytes, CWA source and time window, transformed bytes, mapper report, and native UI result. Remove credentials and precise personal location before considering any artifact for Git.

Compare final decoded getter values with both `report.after` and the source snapshot. Define float tolerances. A validated assignment that equals the original value counts as source coverage but not as a byte modification.

Confirm the exit node and network remain constant for the run and restore prior client preferences afterward. Existing cities may hit native caches; use a new supported city when a fresh response is required.

## Repository verification

`scripts/verify_repo.py` checks documentation links, tracked-file policy, source manifests, and likely secrets. `scripts/test.sh` runs the offline program suites. Platform, timestamp, exit code, and test count belong in a dated evidence file when the result is used for a release or deployment claim.

Do not rerun unaffected suites merely to increase the test count. Rerun the narrow affected checks after a documentation-only change, and escalate only when the changed behavior requires it.
