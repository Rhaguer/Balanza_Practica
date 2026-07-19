#!/usr/bin/env bash
set -euo pipefail

INSTALL_TOOLS=false
for arg in "$@"; do
  case "$arg" in
    --install-tools) INSTALL_TOOLS=true ;;
    *) echo "Parametro no reconocido: $arg" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON=""
for candidate in "$ROOT/.venv/bin/python" "$ROOT/venv/bin/python" "$ROOT/env_unix/bin/python"; do
  if [ -x "$candidate" ]; then
    PYTHON="$candidate"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  PYTHON="python3"
fi

OUT_DIR="${PROJECT_ARTIFACTS_DIR:-$(dirname "$ROOT")/Archivos personales Proyecto Balanza/Resultados}/security"
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$OUT_DIR/security_check_$STAMP.txt"

run_step() {
  local name="$1"
  shift
  {
    echo "===== $name ====="
    "$@"
    echo
  } 2>&1 | tee -a "$LOG"
}

if [ "$INSTALL_TOOLS" = true ]; then
  run_step "Instalar herramientas dev" "$PYTHON" -m pip install -r requirements-dev.txt
fi

run_step "Django check" "$PYTHON" manage.py check
run_step "Django deploy check con perfil seguro" bash "$ROOT/scripts/deploy_check.sh"
run_step "Migraciones pendientes" "$PYTHON" manage.py makemigrations --check --dry-run
run_step "Tests" "$PYTHON" manage.py test
run_step "Dependencias rotas" "$PYTHON" -m pip check
run_step "Bandit SAST" "$PYTHON" -m bandit -r app codigo_qr -x app/migrations,app/tests.py,app/test_weight_bridge.py -f txt -o "$OUT_DIR/bandit_$STAMP.txt"
cat "$OUT_DIR/bandit_$STAMP.txt" | tee -a "$LOG"
run_step "pip-audit dependencias" "$PYTHON" -m pip_audit -r requirements.txt -f json -o "$OUT_DIR/pip_audit_$STAMP.json"

if [ -n "${DAST_TARGET_URL:-}" ]; then
  run_step "DAST smoke local" "$PYTHON" scripts/dast_smoke.py "$DAST_TARGET_URL"
fi
cat "$OUT_DIR/pip_audit_$STAMP.json" | tee -a "$LOG"

echo "Reporte principal: $LOG"
