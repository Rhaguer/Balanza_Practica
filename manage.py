#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True


def start_code_backup_watcher():
    """Activa el espejo único del código durante el servidor de desarrollo."""
    if len(sys.argv) < 2 or sys.argv[1] != "runserver":
        return

    root = Path(__file__).resolve().parent
    script = root / "scripts" / "watch_code_backup.py"
    if not script.exists():
        return

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
        subprocess,
        "DETACHED_PROCESS",
        0,
    )
    try:
        subprocess.Popen(
            [
                sys.executable,
                str(script),
            ],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
    except OSError:
        # El servidor puede continuar aunque el sistema no permita iniciar el vigilante.
        pass


def main():
    """Run administrative tasks."""
    start_code_backup_watcher()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codigo_qr.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
