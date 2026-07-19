#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HOST_ADDRESS="${HOST_ADDRESS:-127.0.0.1}"
PORT="${PORT:-8000}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"
NO_BROWSER="${NO_BROWSER:-0}"

find_python() {
  local candidates=(
    "$ROOT/.venv/bin/python"
    "$ROOT/venv/bin/python"
    "$ROOT/.venv_unix/bin/python"
    "$ROOT/.venv_linux/bin/python"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -x "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done

  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv_unix
  elif command -v python >/dev/null 2>&1; then
    python -m venv .venv_unix
  else
    echo "No se encontro Python. Instale Python 3.12 o superior." >&2
    return 1
  fi

  echo "$ROOT/.venv_unix/bin/python"
}

if [[ ! -f .env ]]; then
  bash scripts/setup.sh
fi

PYTHON="$(find_python)"

ARGS=(scripts/auto_start.py --host "$HOST_ADDRESS" --port "$PORT")
if [[ "$SKIP_INSTALL" == "1" ]]; then
  ARGS+=(--skip-install)
fi
if [[ "$NO_BROWSER" == "1" ]]; then
  ARGS+=(--no-browser)
fi

"$PYTHON" "${ARGS[@]}"
