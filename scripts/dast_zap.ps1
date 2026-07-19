param(
    [string]$TargetUrl = "http://host.docker.internal:8000",
    [string]$ReportName = "zap_baseline.html"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker no esta instalado. Instale Docker Desktop o ejecute OWASP ZAP manualmente."
}

$OutDir = Join-Path (Split-Path $Root -Parent) "Archivos personales Proyecto Balanza\Resultados\security"
New-Item -ItemType Directory -Force $OutDir | Out-Null

docker run --rm -t `
    -v "${OutDir}:/zap/wrk" `
    ghcr.io/zaproxy/zaproxy:stable `
    zap-baseline.py -t $TargetUrl -r $ReportName

Write-Host "Reporte DAST: $(Join-Path $OutDir $ReportName)"
