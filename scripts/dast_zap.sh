#!/usr/bin/env bash
set -euo pipefail

TARGET_URL="${1:-http://host.docker.internal:8000}"
REPORT_NAME="${2:-zap_baseline.html}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker no esta instalado. Instale Docker o ejecute OWASP ZAP manualmente." >&2
  exit 1
fi

OUT_DIR="${PROJECT_ARTIFACTS_DIR:-$(dirname "$ROOT")/Archivos personales Proyecto Balanza/Resultados}/security"
mkdir -p "$OUT_DIR"

docker run --rm -t \
  -v "$OUT_DIR:/zap/wrk" \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t "$TARGET_URL" -r "$REPORT_NAME"

echo "Reporte DAST: $OUT_DIR/$REPORT_NAME"
