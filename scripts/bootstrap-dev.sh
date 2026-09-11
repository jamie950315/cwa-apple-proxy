#!/bin/bash
# Install into this repository's isolated environment only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
UV="${UV_BIN:-$(command -v uv || true)}"
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
if [ -z "$UV" ]; then echo 'Install uv for this user, then rerun.' >&2; exit 2; fi
command -v node >/dev/null || { echo 'Node.js is required.' >&2; exit 2; }
mkdir -p logs data
if [ ! -x .venv/bin/python ]; then "$UV" venv --python "${PYTHON_VERSION:-3.13.5}" .venv; fi
LOCK=requirements.development.lock
if [ "$(uname -s)" = Darwin ] && [ -f requirements.macos.lock ]; then LOCK=requirements.macos.lock; fi
"$UV" pip install --python .venv/bin/python -r "$LOCK"
.venv/bin/python --version
node --version
printf '%s\n' 'Development environment ready. Run ./scripts/test.sh'
