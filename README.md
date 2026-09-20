# CWA Apple Proxy

CWA Apple Proxy keeps the native Apple Weather interface while replacing supported Taiwan weather fields with data from Taiwan's Central Weather Administration (CWA). A Raspberry Pi 5 intercepts opted-in WeatherKit traffic, fetches and normalizes CWA products, rewrites known `WK2.Weather` FlatBuffers fields, and preserves the original Apple response whenever a mapping is unsupported or translation fails.

## Current status

| Component | Status |
|---|---|
| Data translation | `0.3.2`, deployed on the Pi 5 |
| Network transport | `1.0.2`, deployed |
| Repository | Public GitHub repository; `main` is the active branch |
| Runtime | `/home/jamie/cwa-weather-proxy` on the Pi 5 |
| Development checkout | `/Users/jamie/cwa-apple-proxy` on macOS |
| Enrolled clients | Mac and iPhone 14 Pro; enrollment remains opt-in |
| Apple Watch | Working after installing the custom CA on the Watch; successful watchOS transformations were observed |
| Exit nodes | None, the Pi 5, or another working exit node; WeatherKit traffic remains split through the Pi 5 |
| Diagnostics | `http://100.78.140.101:18880/` from the tailnet |
| Main known limitation | The native `TAIWAN_AQI` scale endpoint returns 404, so the complete AQI card is not yet compatible |

Version 0.3.2 prioritizes source accuracy over overwrite count. It uses coherent station thermodynamics, exact hourly forecast points and probability windows, complete precipitation windows, and explicitly derived calendar-day extrema. Unsupported or incompatible groups remain Apple data. The project does not claim that forecasts are error-free or that every visible field comes from CWA.

## Validate the checkout

```sh
cd ~/cwa-apple-proxy
./scripts/bootstrap-dev.sh
./scripts/test.sh
python3 scripts/verify_repo.py
```

The bootstrap creates a repository-local `.venv`. Node tests use the vendored codec and the built-in test runner. Offline tests use fixed fixtures and mocks; production credentials remain on the Pi 5.

The Mac checkout is intended for development, review, and offline verification. The live runtime depends on Linux systemd, nftables, Tailscale, and AdGuard Home. Read [Development](docs/DEVELOPMENT.md) before attempting to run the full service outside the Pi 5.

## Documentation

| Document | Purpose |
|---|---|
| [Status](docs/STATUS.md) | Deployed state, verified behavior, and evidence boundaries |
| [Architecture](docs/ARCHITECTURE.md) | Request flow, services, ports, and modules |
| [Data sources](docs/DATA_SOURCES.md) | CWA and Apple field ownership, time windows, and derivations |
| [Accuracy and coverage](docs/ACCURACY_COVERAGE.md) | Rationale and evidence behind the 0.3.2 mapping policy |
| [Networking](docs/NETWORKING.md) | DNS, split routing, exit-node coexistence, and client enrollment |
| [Operations](docs/OPERATIONS.md) | Health checks, deployment, rollback, certificates, and diagnostics |
| [Development](docs/DEVELOPMENT.md) | Dependencies, tests, fixtures, and platform constraints |
| [Validation](docs/VALIDATION.md) | What each evidence layer proves and does not prove |
| [Known issues](docs/KNOWN_ISSUES.md) | Active limitations and future work |
| [Decisions](docs/DECISIONS.md) | Current architectural decisions and rejected approaches |
| [Security](docs/SECURITY.md) | Secrets, certificates, private evidence, and public-repository boundaries |
| [Provenance](docs/PROVENANCE.md) | Source snapshots, manifests, and archived evidence |
| [Performance](docs/PERFORMANCE.md) | Cache behavior and measured latency |
| [Changelog](docs/CHANGELOG.md) | Version and deployment history |

`systemd/` contains source unit files, while `infra/live-systemd/` contains captured installed units for comparison. `docs/history/` contains dated reports; they describe the state at the time of each test and are not current operating instructions. Private raw captures and precise location evidence are excluded from Git.

## License

The project-specific code remains `UNLICENSED`; making the repository public does not grant a license to use, copy, or redistribute that code. The vendored codec retains its Apache-2.0 license and NOTICE. Third-party research material remains subject to its original license.
