# Source provenance and retained evidence

The authoritative initial source extraction came from `/home/jamie/cwa-weather-proxy` on the Pi 5. `docs/evidence/production-source-manifest.json` records source paths, SHA-256 hashes, sizes, and redaction flags at that date. Later deployments are documented separately; the initial manifest is not a claim that production never changed.

## Storage layers

| Path | Contents |
|---|---|
| Root source, `vendor/`, `tests/`, `systemd/`, `config/` | Maintained program, required configuration, and tests |
| `infra/live-systemd/` | Captured installed units; distinguish them from source units |
| `infra/snapshots/` | Dated service, Serve, route, DNS, nftables, and dependency snapshots |
| `docs/reference/` | CWA API schemas, GRIB metadata, and native codec research |
| `docs/history/` | Dated deployment and acceptance reports; historical, not current instructions |
| `tools/history/` | One-off research and patch scripts; read-only reference |
| `.private/history.tar.gz` | Excluded raw research, logs, schemas, failures, and reports |
| `.private/native-evidence.tar.gz` | Excluded native payloads, mapper reports, and source snapshots |
| `.private/runtime/` | Excluded client, managed-DNS, route ownership, and public-CA snapshots |
| `.private/provenance/history-manifest.json` | Excluded archive hashes, redactions, and omission reasons |

Reproducible environments, temporary PIDs, large GRIB downloads, secrets, and private keys are omitted from Git. Native proof storage had a rolling limit, so evidence that had already rotated away is not claimed as recovered.

Current technical state is documented in [Status](STATUS.md), while decisions and evolution are in [Decisions](DECISIONS.md) and [Changelog](CHANGELOG.md). Always pair a dated report with live verification when making an operational claim.
