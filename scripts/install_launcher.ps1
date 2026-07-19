param(
    [switch]$NoAutoStart
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Find-Pythonw {
    $Candidates = @(
        (Join-Path $Root "venv\Scripts\pythonw.exe"),
        (Join-Path $Root ".venv\Scripts\pythonw.exe"),
        (Join-Path $Root ".venv_win\Scripts\pythonw.exe"),
        (Join-Path $Root "env_win\Scripts\pythonw.exe")
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate) {
            return $Candidate
        }
    }
    throw "No se encontró el entorno Python. Ejecute primero INSTALAR_ACCESO_DIRECTO.bat."
}

function New-AppShortcut {
    param(
        [string]$Path,
        [string]$Pythonw
    )

    $Shell = New-Object -ComObject WScript.Shell
    $Shortcut = $Shell.CreateShortcut($Path)
    $Shortcut.TargetPath = $Pythonw
    $Shortcut.Arguments = "`"$Root\scripts\auto_start.py`" --skip-install"
    $Shortcut.WorkingDirectory = $Root
    $Shortcut.Description = "Iniciar Balanza de Mermas"
    $Shortcut.IconLocation = "$Pythonw,0"
    $Shortcut.Save()
}

$Pythonw = Find-Pythonw
$Desktop = [Environment]::GetFolderPath("Desktop")
$DesktopShortcut = Join-Path $Desktop "Balanza de Mermas.lnk"
New-AppShortcut -Path $DesktopShortcut -Pythonw $Pythonw

if (-not $NoAutoStart) {
    $Startup = [Environment]::GetFolderPath("Startup")
    $StartupShortcut = Join-Path $Startup "Balanza de Mermas.lnk"
    New-AppShortcut -Path $StartupShortcut -Pythonw $Pythonw
}

Write-Output "Acceso directo creado: $DesktopShortcut"
if (-not $NoAutoStart) {
    Write-Output "Inicio automático activado para la sesión de Windows."
}
