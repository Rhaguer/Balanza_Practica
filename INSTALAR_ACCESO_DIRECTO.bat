@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" if not exist ".venv\Scripts\python.exe" if not exist ".venv_win\Scripts\python.exe" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\setup.ps1"
    if errorlevel 1 goto :error
)

set "PYTHON=venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=.venv_win\Scripts\python.exe"

"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :error
"%PYTHON%" manage.py migrate --noinput
if errorlevel 1 goto :error
"%PYTHON%" manage.py collectstatic --noinput
if errorlevel 1 goto :error

powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_launcher.ps1"
if errorlevel 1 goto :error

echo.
echo Instalacion terminada. Use "Balanza de Mermas" en el escritorio.
pause
exit /b 0

:error
echo.
echo No se pudo completar la instalacion. Revise el mensaje anterior.
pause
exit /b 1
