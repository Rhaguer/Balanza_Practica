#!/usr/bin/env bash
set -euo pipefail

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

random_secret() {
  "$PYTHON" - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
}

export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY="$(random_secret)"
export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1}"
export DJANGO_CSRF_TRUSTED_ORIGINS="${DJANGO_CSRF_TRUSTED_ORIGINS:-https://localhost,https://127.0.0.1}"
export DJANGO_SECURE_SSL_REDIRECT=True
export DJANGO_USE_X_FORWARDED_PROTO=True
export DJANGO_HEALTH_CHECK_REQUIRE_LOGIN=True
export DJANGO_HEALTH_CHECK_EXPOSE_DETAILS=False
export WEIGHT_API_TOKEN="$(random_secret)"

"$PYTHON" manage.py check --deploy
