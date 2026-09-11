#!/bin/bash
# Offline regression tests use mock HTTP and the recorded city fixture.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -x .venv/bin/python ] || { echo 'Run ./scripts/bootstrap-dev.sh first.' >&2; exit 2; }
mkdir -p logs
.venv/bin/python -m pytest tests -q
node --test tests/*.test.mjs
.venv/bin/python scripts/verify_repo.py
