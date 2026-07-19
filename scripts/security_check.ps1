param(
    [switch]$InstallTools,
    [string]$DastTargetUrl = ""
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

$OutDir = Join-Path (Split-Path $Root -Parent) "Archivos personales Proyecto Balanza\Resultados\security"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Log = Join-Path $OutDir "security_check_$Stamp.txt"
$PowerShell = (Get-Process -Id $PID).Path

function Run-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    "===== $Name =====" | Tee-Object -FilePath $Log -Append
    $PreviousErrorActionPreference = $ErrorActionPreference
    try {
        # Windows PowerShell convierte cualquier stderr nativo en NativeCommandError
        # cuando ErrorActionPreference es Stop, aunque el proceso termine con código 0.
        $ErrorActionPreference = "Continue"
        $global:LASTEXITCODE = 0
        & $Command 2>&1 |
            ForEach-Object { $_.ToString() } |
            Tee-Object -FilePath $Log -Append
        $ExitCode = $LASTEXITCODE
        if ($ExitCode -ne 0) {
            throw "$Name falló con código de salida $ExitCode."
        }
    } catch {
        $_ | Tee-Object -FilePath $Log -Append
        throw
    } finally {
        $ErrorActionPreference = $PreviousErrorActionPreference
    }
    "" | Tee-Object -FilePath $Log -Append
}

if ($InstallTools) {
    Run-Step "Instalar herramientas dev" { & $Python -m pip install -r requirements-dev.txt }
}

Run-Step "Django check" { & $Python manage.py check }
Run-Step "Django deploy check con perfil seguro" {
    & $PowerShell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\deploy_check.ps1")
}
Run-Step "Migraciones pendientes" { & $Python manage.py makemigrations --check --dry-run }
Run-Step "Tests" { & $Python manage.py test }
Run-Step "Dependencias rotas" { & $Python -m pip check }

Run-Step "Bandit SAST" {
    & $Python -m bandit -r app codigo_qr -x app/migrations,app/tests.py,app/test_weight_bridge.py -f txt -o (Join-Path $OutDir "bandit_$Stamp.txt")
    Get-Content (Join-Path $OutDir "bandit_$Stamp.txt")
}

Run-Step "pip-audit dependencias" {
    & $Python -m pip_audit -r requirements.txt -f json -o (Join-Path $OutDir "pip_audit_$Stamp.json")
    Get-Content (Join-Path $OutDir "pip_audit_$Stamp.json")
}

if ($DastTargetUrl) {
    Run-Step "DAST smoke local" { & $Python scripts\dast_smoke.py $DastTargetUrl }
}

Write-Host "Reporte principal: $Log"
