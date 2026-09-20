# CWA Apple Proxy - Repository Instructions

## Start here

Read `docs/STATUS.md`, `docs/ARCHITECTURE.md`, `docs/KNOWN_ISSUES.md`, and `docs/OPERATIONS.md` before changing runtime behavior. Read `docs/evidence/repo-verification.json` for checkout verification and `docs/evidence/production-source-manifest.json` for the original production-source hashes.

The development checkout is `/Users/jamie/cwa-apple-proxy`. The deployed runtime is `/home/jamie/cwa-weather-proxy` on the Pi 5. The repository is public at `jamie950315/cwa-apple-proxy`; secrets, private keys, raw locations, and private captures must never be committed.

Current versions are data translation **0.3.2** and network transport **1.0.2**. The Mac and iPhone are enrolled. Apple Watch Weather works after the Watch received the custom CA, and successful watchOS transformations have been observed. Exit nodes may be None, the Pi 5, or another working node. The `jarvis` host is intentionally outside the project scope.

## Working rules

- Communicate with Jamie in Traditional Chinese. Repository content, code comments, UI text, tests, and documentation are English unless a source artifact must retain its original language.
- Verify current services and source before relying on dated evidence. Historical reports remain evidence for their stated date only.
- A checkout change does not authorize a production deployment. Record code, test, deployment, and device/UI evidence separately.
- Distinguish configuration saved, route advertised, route approved, client route received, HTTPS completed, response transformed, payload decoded, and native UI displayed. Each requires its own evidence.
- `skippedFields=0` means all eligible writes in that response succeeded; it does not mean that every Apple field was replaced.
- Version 0.3.2 uses coherent same-station thermodynamics, exact hourly forecast points and PoP windows, whole precipitation windows, compatible precipitation companions, and explicitly derived 00:00-24:00 extrema with occurrence times. Unsupported groups remain Apple. Never describe forecasts as error-free.
- Do not restore removed PoP/rainfall disaggregation or temperature interpolation without independent calibration and acceptance evidence. Do not enable the unverified WRF +78/+84-hour extension.
- Keep the 3.5-second translation deadline, original-body/header fallback, asynchronous ntfy notification, and 300-second deduplication unless a task explicitly changes that contract.
- Preserve device opt-in. Enable a new client only after its device trusts the name-constrained CA. Do not revert the enrolled Mac or iPhone to pending state.
- Keep production secrets in the Pi 5 `.env` and `certs`. `.private` is local-only. Unknown FlatBuffers slots must remain byte-compatible across rewrites.
- Do not remotely control the user's iPhone while they are away from the Mac. Ask only if physical device interaction is indispensable.

## Safe entry points

```sh
cd ~/cwa-apple-proxy
./scripts/bootstrap-dev.sh
./scripts/test.sh
python3 scripts/verify_repo.py
./scripts/pi-status.sh
```

`systemd/`, `bridgectl.py`, `network_rules.py`, and `split_routes.py` are Pi 5/Linux operational tools. Do not run mutating operations from macOS. `tools/history/` contains one-off historical scripts with old paths and potentially destructive behavior; treat it as read-only reference material.

After substantive work, update current documentation, `docs/KNOWN_ISSUES.md`, applicable evidence, and `docs/CHANGELOG.md`. Commit coherent milestones. Production deployment and GitHub publishing remain separate actions and require the current task to authorize them.
