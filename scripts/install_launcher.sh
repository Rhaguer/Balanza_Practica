#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OS="$(uname -s)"

if [[ ! -x "$ROOT/.venv/bin/python" && ! -x "$ROOT/venv/bin/python" && ! -x "$ROOT/.venv_unix/bin/python" && ! -x "$ROOT/.venv_linux/bin/python" ]]; then
  bash "$ROOT/scripts/setup.sh"
fi

PYTHON="$ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="$ROOT/venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="$ROOT/.venv_unix/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="$ROOT/.venv_linux/bin/python"

"$PYTHON" -m pip install -r "$ROOT/requirements.txt"
"$PYTHON" "$ROOT/manage.py" migrate --noinput
"$PYTHON" "$ROOT/manage.py" collectstatic --noinput

if [[ "$OS" == "Linux" ]]; then
  BIN_DIR="$HOME/.local/bin"
  APP_DIR="$HOME/.local/share/applications"
  AUTOSTART_DIR="$HOME/.config/autostart"
  mkdir -p "$BIN_DIR" "$APP_DIR" "$AUTOSTART_DIR"

  LAUNCHER="$BIN_DIR/balanza-mermas"
  printf '#!/usr/bin/env bash\nnohup bash %q </dev/null >>%q 2>&1 &\n' \
    "$ROOT/scripts/start_all.sh" "$HOME/.balanza-mermas-inicio.log" >"$LAUNCHER"
  chmod +x "$LAUNCHER"

  DESKTOP_FILE="$APP_DIR/balanza-mermas.desktop"
  cat >"$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Balanza de Mermas
Comment=Iniciar aplicación y conexión con la balanza
Exec=$LAUNCHER
Terminal=false
Categories=Office;
EOF
  cp "$DESKTOP_FILE" "$AUTOSTART_DIR/balanza-mermas.desktop"
  chmod +x "$DESKTOP_FILE" "$AUTOSTART_DIR/balanza-mermas.desktop"
  echo "Acceso de Linux instalado y arranque automático activado."
elif [[ "$OS" == "Darwin" ]]; then
  COMMAND="$HOME/Desktop/Balanza de Mermas.command"
  mkdir -p "$HOME/Desktop" "$HOME/Library/LaunchAgents"
  printf '#!/usr/bin/env bash\nnohup bash %q </dev/null >>%q 2>&1 &\n' \
    "$ROOT/scripts/start_all.sh" "$HOME/.balanza-mermas-inicio.log" >"$COMMAND"
  chmod +x "$COMMAND"

  PLIST="$HOME/Library/LaunchAgents/cl.inacap.balanza-mermas.plist"
  ESCAPED_ROOT="${ROOT//&/&amp;}"
  cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>cl.inacap.balanza-mermas</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$ESCAPED_ROOT/scripts/start_all.sh</string></array>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$HOME/.balanza-mermas-inicio.log</string>
  <key>StandardErrorPath</key><string>$HOME/.balanza-mermas-inicio.log</string>
</dict>
</plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "Acceso de macOS instalado y arranque automático activado."
else
  echo "Sistema no compatible con este instalador: $OS" >&2
  exit 1
fi
