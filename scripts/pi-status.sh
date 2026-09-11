#!/bin/bash
# Read-only health inspection of the existing Pi5 deployment.
set -euo pipefail
ssh -o BatchMode=yes -o ConnectTimeout=8 "${PI_SSH:-jamie@100.78.140.101}" 'cd /home/jamie/cwa-weather-proxy && date -Is && systemctl list-units "cwa-weather*" --all --no-pager && .venv/bin/python bridgectl.py status && .venv/bin/python split_routes.py status && curl -fsS --max-time 10 http://100.78.140.101:18880/healthz'
