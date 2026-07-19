#!/usr/bin/env bash
set -euo pipefail

PRODUCTION=false
SKIP_INSTALL=false

for arg in "$@"; do
  case "$arg" in
    --production) PRODUCTION=true ;;
    --skip-install) SKIP_INSTALL=true ;;
    *) echo "Parametro no reconocido: $arg" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 no esta disponible en PATH." >&2
  exit 1
fi

VENV_PYTHON=""
for candidate in "$ROOT/.venv/bin/python" "$ROOT/venv/bin/python" "$ROOT/.venv_unix/bin/python" "$ROOT/.venv_linux/bin/python" "$ROOT/env_unix/bin/python"; do
  if [ -x "$candidate" ]; then
    VENV_PYTHON="$candidate"
    break
  fi
done

if [ -z "$VENV_PYTHON" ]; then
  TARGET_VENV=".venv"
  if [ -d ".venv" ]; then
    TARGET_VENV=".venv_unix"
  fi
  python3 -m venv "$TARGET_VENV"
  VENV_PYTHON="$ROOT/$TARGET_VENV/bin/python"
fi

if [ "$SKIP_INSTALL" = false ]; then
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -r requirements.txt
fi

random_secret() {
  "$VENV_PYTHON" - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
}

if [ ! -f ".env" ]; then
  if [ "$PRODUCTION" = true ]; then
    DEBUG_VALUE="False"
    SECURE_REDIRECT="True"
    HEALTH_REQUIRE_LOGIN="True"
  else
    DEBUG_VALUE="True"
    SECURE_REDIRECT="False"
    HEALTH_REQUIRE_LOGIN="False"
  fi

  SECRET_KEY="$(random_secret)"
  WEIGHT_TOKEN="$(random_secret)"

  cat > .env <<EOF
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=$DEBUG_VALUE
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
DJANGO_PUBLIC_BASE_URL=
DJANGO_DB_NAME=../Datos Proyecto Balanza/db.sqlite3
DJANGO_STATIC_ROOT=../Datos Proyecto Balanza/staticfiles
DJANGO_MEDIA_ROOT=../Datos Proyecto Balanza/media
DJANGO_EXPORT_DIR=../Datos Proyecto Balanza/Excel por Taller
DJANGO_BACKUP_DIR=../Datos Proyecto Balanza/backups
DJANGO_LOG_DIR=../Datos Proyecto Balanza/logs
WORKSHOP_WORKER_INTERVAL_SECONDS=10
DJANGO_SESSION_COOKIE_AGE=14400
DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE=False
DJANGO_HSTS_SECONDS=31536000
DJANGO_SECURE_SSL_REDIRECT=$SECURE_REDIRECT
DJANGO_USE_X_FORWARDED_PROTO=False
DJANGO_TRUSTED_PROXY_IPS=
DJANGO_LOG_LEVEL=INFO
DJANGO_HEALTH_CHECK_REQUIRE_LOGIN=$HEALTH_REQUIRE_LOGIN
DJANGO_HEALTH_CHECK_EXPOSE_DETAILS=False
DJANGO_WEIGHT_UPDATE_URL=/api/update_weight/
WEIGHT_API_TOKEN=$WEIGHT_TOKEN
MAX_WEIGHT_KG=1000
WEIGHT_READING_MAX_AGE_SECONDS=10
WEIGHT_BRIDGE_FIRST=True
WEIGHT_DIRECT_READ_ENABLED=True
BALANZA_SERIAL_PORTS=
BALANZA_SERIAL_BAUDRATES=9600,4800,2400,1200,19200,38400,57600,115200
BALANZA_SERIAL_MODES=8N1,7E1,8E1,7N1,8N2
BALANZA_LINE_CONTROLS=default,rts,dtr_rts,none
BALANZA_READ_SECONDS=4
BALANZA_STABLE_SAMPLES=3
BALANZA_STABLE_TOLERANCE_KG=0.020
BALANZA_DIRECT_MAX_ATTEMPTS=32
BALANZA_POLL_COMMANDS=S\r\n,W\r\n,P\r\n,SI\r\n,Q\r\n,PRINT\r\n
PASSWORD_MAX_AGE_DAYS=120
ENFORCE_INSTITUTIONAL_EMAIL_DOMAIN=True
INSTITUTIONAL_EMAIL_DOMAINS=inacap.cl,inacapmail.cl
USE_INSTITUTIONAL_BRAND=False
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_SECONDS=900
DATA_RETENTION_DAYS=1095
AUDIT_LOG_RETENTION_DAYS=365
WEIGHT_READING_RETENTION_DAYS=365
BACKUP_RETENTION_DAYS=180
EOF
  echo "Se genero .env con secretos locales aleatorios."
fi

"$VENV_PYTHON" manage.py migrate
"$VENV_PYTHON" manage.py check
"$VENV_PYTHON" manage.py collectstatic --noinput
"$VENV_PYTHON" scripts/sync_code_backup.py

cat <<'EOF'

Listo. Para ejecutar:
bash scripts/install_launcher.sh

Si no hay usuario administrador:
python manage.py createsuperuser
EOF
