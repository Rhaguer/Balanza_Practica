param(
    [switch]$Production,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function New-RandomSecret {
    param([int]$Bytes = 48)
    $buffer = New-Object byte[] $Bytes
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($buffer)
    }
    finally {
        $generator.Dispose()
    }
    return [Convert]::ToBase64String($buffer).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

$PythonLauncher = "python"
$PythonPrefixArgs = @()
if (-not (Get-Command $PythonLauncher -ErrorAction SilentlyContinue)) {
    $PythonLauncher = "py"
    $PythonPrefixArgs = @("-3")
}
if (-not (Get-Command $PythonLauncher -ErrorAction SilentlyContinue)) {
    throw "Python no esta disponible en PATH. Instale Python 3.12 o superior."
}

$CandidatePythons = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    (Join-Path $Root "venv\Scripts\python.exe"),
    (Join-Path $Root "env_win\Scripts\python.exe"),
    (Join-Path $Root ".venv\bin\python")
)
$VenvPython = $CandidatePythons | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $VenvPython) {
    $TargetVenv = if (Test-Path ".venv") { ".venv_win" } else { ".venv" }
    & $PythonLauncher @PythonPrefixArgs -m venv $TargetVenv
    $VenvPython = Join-Path $Root "$TargetVenv\Scripts\python.exe"
}

if (-not (Test-Path $VenvPython)) {
    throw "No se encontro un Python valido de entorno virtual."
}

if (-not $SkipInstall) {
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    $DebugValue = if ($Production) { "False" } else { "True" }
    $SecureRedirect = if ($Production) { "True" } else { "False" }
    $HealthRequireLogin = if ($Production) { "True" } else { "False" }
    $SecretKey = New-RandomSecret 64
    $WeightToken = New-RandomSecret 48

    @"
DJANGO_SECRET_KEY=$SecretKey
DJANGO_DEBUG=$DebugValue
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
DJANGO_SECURE_SSL_REDIRECT=$SecureRedirect
DJANGO_USE_X_FORWARDED_PROTO=False
DJANGO_TRUSTED_PROXY_IPS=
DJANGO_LOG_LEVEL=INFO
DJANGO_HEALTH_CHECK_REQUIRE_LOGIN=$HealthRequireLogin
DJANGO_HEALTH_CHECK_EXPOSE_DETAILS=False
DJANGO_WEIGHT_UPDATE_URL=/api/update_weight/
WEIGHT_API_TOKEN=$WeightToken
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
"@ | Set-Content -Encoding UTF8 ".env"

    Write-Host "Se genero .env con secretos locales aleatorios."
}

& $VenvPython manage.py migrate
& $VenvPython manage.py check
& $VenvPython manage.py collectstatic --noinput
& $VenvPython (Join-Path $Root "scripts\sync_code_backup.py") | Out-Null

Write-Host ""
Write-Host "Listo. Para ejecutar:"
Write-Host "Use el entorno detectado en: $VenvPython"
Write-Host "Use INSTALAR_ACCESO_DIRECTO.bat o scripts\start_all.ps1"
Write-Host ""
Write-Host "Si no hay usuario administrador:"
Write-Host "python manage.py createsuperuser"
