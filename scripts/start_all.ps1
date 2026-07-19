param(
    [string]$HostAddress = "127.0.0.1",
    [string]$Port = "8000",
    [switch]$SkipInstall,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Find-Python {
    $candidates = @(
        (Join-Path $Root "venv\Scripts\python.exe"),
        (Join-Path $Root "env_win\Scripts\python.exe"),
        (Join-Path $Root ".venv_win\Scripts\python.exe"),
        (Join-Path $Root ".venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonLauncher) {
        py -3 -m venv .venv_win
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv .venv_win
    } else {
        throw "No se encontro Python. Instale Python 3.12 o superior antes de ejecutar el proyecto."
    }

    $created = Join-Path $Root ".venv_win\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $created)) {
        throw "No se pudo crear el entorno virtual Windows."
    }
    return $created
}

if (-not (Test-Path -LiteralPath ".env")) {
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
}

$Python = Find-Python
$argsAuto = @(
    ".\scripts\auto_start.py",
    "--host", $HostAddress,
    "--port", $Port
)
if ($SkipInstall) {
    $argsAuto += "--skip-install"
}
if ($NoBrowser) {
    $argsAuto += "--no-browser"
}

& $Python @argsAuto
