# Security and data boundaries

This repository is public. Production credentials remain in the Pi 5 mode-0600 `.env`. The CA private key and WeatherKit leaf/private-key bundle remain under the Pi 5 `certs/` directory and must never be copied into Git.

The local `.private` directory contains raw research, payloads, public-CA material, station/location history, client addresses, and old exit-node evidence. It is mode-restricted and ignored. Public fixtures contain only fixed test-city coordinates and no authentication headers.

Historical scripts have CWA keys replaced with `REDACTED_CWA_API_KEY`. Public-source review must still account for personal network topology, protocol research, and third-party licensing.

The CA is constrained to `weatherkit.apple.com`. Do not regenerate or replace the trusted CA as part of repository setup. The leaf certificate requires periodic renewal.

CWA TLS keeps certificate and hostname verification. The runtime relaxes only an OpenSSL strict-extension compatibility check observed with the CWA chain. Do not introduce `verify=False` or `curl -k` as a production default.

The ntfy topic is publicly guessable. Notifications exclude coordinates, API keys, and tokens. Access-controlled notification delivery would require a separate design.

`/status` may expose location, proof, and certificate metadata. Keep it tailnet-only; do not publish it through an unrestricted reverse proxy.

## Before committing

```sh
python3 scripts/verify_repo.py --staged
```

The pre-commit hook scans staged bytes for likely CWA keys, private-key blocks, and prohibited paths. `.gitignore` is not sufficient protection because `git add -f` can bypass it. Review the staged diff and repository history before every public push.
