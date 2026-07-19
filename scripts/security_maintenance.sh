#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="python3"
for candidate in "$ROOT/.venv/bin/python" "$ROOT/venv/bin/python" "$ROOT/env_unix/bin/python"; do
  if [ -x "$candidate" ]; then
    PYTHON="$candidate"
    break
  fi
done

ARGS=(manage.py security_maintenance)
if [ "${1:-}" = "--purge-data" ]; then
  ARGS+=(--purge-data)
fi

"$PYTHON" "${ARGS[@]}"
