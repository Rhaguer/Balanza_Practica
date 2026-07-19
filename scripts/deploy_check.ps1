param(
    [string]$AllowedHosts = "localhost,127.0.0.1",
    [string]$CsrfOrigins = "https://localhost,https://127.0.0.1"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function New-RandomSecret {
    $buffer = New-Object byte[] 64
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($buffer)
    } finally {
        $generator.Dispose()
    }
    return [Convert]::ToBase64String($buffer).TrimEnd("=").Replace("+", "-").Replace("/", "_")
}

$CandidatePythons = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    (Join-Path $Root "venv\Scripts\python.exe"),
    (Join-Path $Root "env_win\Scripts\python.exe"),
    (Join-Path $Root ".venv\bin\python")
)
$Python = $CandidatePythons | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Python) {
    $Python = "python"
}

$env:DJANGO_DEBUG = "False"
$env:DJANGO_SECRET_KEY = New-RandomSecret
$env:DJANGO_ALLOWED_HOSTS = $AllowedHosts
$env:DJANGO_CSRF_TRUSTED_ORIGINS = $CsrfOrigins
$env:DJANGO_SECURE_SSL_REDIRECT = "True"
$env:DJANGO_USE_X_FORWARDED_PROTO = "True"
$env:DJANGO_HEALTH_CHECK_REQUIRE_LOGIN = "True"
$env:DJANGO_HEALTH_CHECK_EXPOSE_DETAILS = "False"
$env:WEIGHT_API_TOKEN = New-RandomSecret

& $Python manage.py check --deploy
