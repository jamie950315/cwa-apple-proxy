# Operations, deployment, and rollback

## Read-only checks

```sh
cd ~/cwa-apple-proxy
./scripts/pi-status.sh
ssh jamie@100.78.140.101 'cd /home/jamie/cwa-weather-proxy && .venv/bin/python bridgectl.py status && .venv/bin/python split_routes.py status'
```

`/healthz` reports the service version and fetch/cache health. `/status` reports enrolled clients, recent transformations, codec, routes, exit compatibility, and notifications. `/v1/cwa/weather?latitude=25.09&longitude=121.56` performs a live source fetch.

Model and route-status systemd units are oneshot jobs, so `inactive (dead)` can mean the last run completed; check their timers. Proxy, API, codec, and SNI services should be active/running. The routing service is expected to be active/exited.

## Safe source deployment

The live API, codec, reverse proxy, and explicit proxy report translation version 0.3.2. Its rollback backup is `backups/accuracy-032-20260920/` on the Pi 5.

1. Read [Status](STATUS.md) and [Known issues](KNOWN_ISSUES.md). Run affected offline tests.
2. Compare live Pi 5 hashes with the relevant evidence or current Git source. Integrate differences instead of overwriting unrelated work.
3. Check active connections. Back up only affected files under `backups/<timestamp>/`, preserving modes and recording service state.
4. Upload reviewed files only. Never copy `.private`, local fixtures, `clients.json`, CA material, or local environment state over production. Do not use `rsync --delete`.
5. Run affected Python/Node tests on the Pi 5. Restart only affected services; run `daemon-reload` only for unit changes.
6. Check health, cache state, and a fresh native response. Decode the final payload field-by-field; validate new UI cards separately.
7. On failure, restore the scoped backup and restart the same services. For a client-specific network problem, prefer `bridgectl disable <IP>` over broad DNS/routing changes.

For a 0.3.2 source rollback, restore the changed modules/dashboard/package and restart `cwa-weather-api`, `cwa-weather-codec`, `cwa-weather-proxy`, and `cwa-weather-forward` after checking activity. Do not restore DNS, certificates, enrollment, or caches; those were not part of the deployment.

Mapper `assignments` counts source-validated writes even when the numeric value was unchanged. `sourceCoverage` classifies official/derived/mixed assignments and is not a percentage. `retainedApple` records guarded groups. The published `/source.zip` and source-catalog `/audit` are historical artifacts, not a current source release.

## Common Pi 5 commands

```sh
cd /home/jamie/cwa-weather-proxy
systemctl status cwa-weather-api cwa-weather-codec cwa-weather-proxy cwa-weather-sni --no-pager
systemctl list-timers 'cwa-weather-*' --all --no-pager
journalctl -u cwa-weather-proxy -n 50 --no-pager
tail -n 5 logs/bridge-reverse.jsonl

# Remove one client from interception.
sudo .venv/bin/python bridgectl.py disable <Tailscale-IP>

# Enroll only after the client fully trusts the CA.
sudo .venv/bin/python bridgectl.py enable <Tailscale-IP> --confirm-certificate-trusted

# Withdraw project-managed relay routes; bridgectl manages DNS separately.
sudo .venv/bin/python split_routes.py withdraw
```

Always read the live Pi 5 client list. Historical snapshots are not enrollment authority.

## New-host reconstruction

Parameterize or explicitly replace `100.78.140.101`, `/home/jamie/cwa-weather-proxy`, `/home/linuxbrew/.linuxbrew/bin/node`, and `/opt/AdGuardHome/AdGuardHome.yaml`. Create project, log, data, certificate, and backup directories with correct ownership. Use Python 3.13 and the production lock, the vendored Node codec, and a mode-0600 `.env`.

Deploy and validate Tailscale and AdGuard separately. Preserve unrelated Tailscale Serve routes. Recreate the TCP/443 SNI path and the HTTPS 18444 paths from [Architecture](ARCHITECTURE.md). Approve relay prefixes and restricted DNS explicitly.

Do not regenerate the existing CA as a side effect. A new CA requires new trust installation and per-device opt-in.

## Certificates and Watch diagnostics

Live AdGuard query logs are under `/var/log/adguard/`; `/opt/AdGuardHome/data/` contains stale January logs. Confirm the live setting before reading logs.

`logs/transport-reverse.jsonl` records privacy-limited `tls-established`, `tls-failed`, and `http-response` events. It omits URLs, coordinates, headers, raw errors, and TLS secrets. Connection IDs correlate transport events but cannot identify the physical client after Tailscale Serve/SNI forwarding.

Tailnet CA downloads:

- `http://100.78.140.101:18880/ca.cer`
- `http://100.78.140.101:18880/CWA-Weather.mobileconfig`

Verified CA DER SHA-256: `002ac26eb292b77d731b0807ca0401fe9becfad64eadbe01ec643023502b5865`. It is constrained to `weatherkit.apple.com`. Apple [QA1948](https://developer.apple.com/library/archive/qa/qa1948/_index.html) requires installing a custom CA on both paired iPhone and Watch.

```sh
openssl x509 -in certs/ca.pem -noout -subject -dates -fingerprint -sha256
openssl x509 -in certs/weatherkit.pem -noout -subject -dates
```

The leaf is approximately one year and the CA approximately ten years. Renewal is manual: sign a new leaf with the existing CA, replace atomically, restart only the proxy, and verify TLS.

The 3.5-second deadline begins after an Apple response exists. Host or transport outages need external monitoring. ntfy tests send real messages; label them TEST and avoid repetition. Notifications must not contain coordinates or credentials.
