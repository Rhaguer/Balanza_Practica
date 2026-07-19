param(
    [switch]$PurgeData
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

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

$Arguments = @("manage.py", "security_maintenance")
if ($PurgeData) {
    $Arguments += "--purge-data"
}

& $Python @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "El mantenimiento de seguridad terminó con errores."
}
