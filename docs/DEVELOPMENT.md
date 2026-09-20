# Development and dependencies

## Versioned environments

The Pi 5 runs Python 3.13.5; its captured package set is in `infra/snapshots/python-freeze.txt`. The original Mac source environment used Python 3.14.7 and Node 23.11.0. Repository bootstrap uses an isolated Python 3.13 environment to stay close to production.

`requirements.production-linux.lock` is the complete deployed environment, including ecCodes, NumPy, pyproj, and binary support packages omitted by the older lock. `requirements.development.lock` keeps the same tested versions while applying Linux-only markers. `requirements.macos.lock` is the tested macOS resolution. `requirements.lock` remains historical reference.

The Node runtime has no network-installed production dependency; the codec is vendored. Translation version and transport version are recorded separately.

## Tests

```sh
./scripts/bootstrap-dev.sh
./scripts/test.sh
python3 scripts/verify_repo.py
```

Tests do not require a real CWA key. HTTP calls use mocks and fixed historical times. The small public fixture uses a fixed city coordinate; complete device locations remain in `.private`.

The suites cover mapping policy, coherent thermodynamics, exact probability/rain windows, daily extrema, omitted scalars, unknown roots, malformed inputs, alert/astronomy roots, proxy filtering and fallback, timeout/notification behavior, routing ranges, and approval semantics.

## Local runtime limits

The source preserves some production paths and addresses. `addon.py` targets the Pi 5 root/API, `codec_server.mjs` binds loopback port 18881, and status handling expects production certificate files and `.env`. Linux units also depend on systemd, nftables, Tailscale, and AdGuard Home.

Use macOS for offline development and verification. Do not fake `/home/jamie` with symlinks or apply Linux units directly to macOS. Generalizing every path into a portable full runtime is a separate project.

## Updating fixtures or the codec

Capture a native response only from an authorized client. Verify country and MIME, remove authentication and personal location data, and select a fixed-city fixture. Freeze `now` so historical observations are not rejected as stale. Store original bytes, normalized CWA data, mapper report, and sanitized request metadata together.

Preserve vendor LICENSE/NOTICE files and update source hashes and rebuild notes for codec changes. Rebuilds of AQI or warning roots must prove that unknown slots and sibling roots remain intact.

## Git and public-repository hygiene

`main` tracks `origin/main` on GitHub. Install the repository hook after cloning:

```sh
git config core.hooksPath .githooks
```

`.private`, `.env`, certificates, runtime caches, `node_modules`, `.venv`, and logs are ignored. Run `python3 scripts/verify_repo.py --staged` before committing. Do not use `git add -f` to bypass a protected path.

## macOS binary packages

The production `eccodeslib 2.48.2.27` wheel is Linux-only. The macOS lock uses a compatible binary selected by the same ecCodes binding. The verified Mac environment used Python 3.13.5, ecCodes 2.48.0, eccodeslib 2.48.0.26, and eckitlib 2.1.1.26; `python -m eccodes selfcheck` loaded `libeccodes.dylib` successfully.

Upstream installation reference: <https://github.com/ecmwf/eccodes-python>.
