#!/usr/bin/env python
"""Mantiene un único espejo del código fuera de la aplicación."""

import argparse
import fnmatch
import shutil
from datetime import datetime
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".agents",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv_linux",
    ".venv_win",
    ".vscode",
    "__pycache__",
    "backups",
    "env_win",
    "exportaciones",
    "logs",
    "media",
    "outputs",
    "staticfiles",
    "tmp",
    "venv",
}
EXCLUDED_FILES = {".env", "db.sqlite3", "desktop.ini", "Thumbs.db"}
EXCLUDED_PATTERNS = ("*.pyc", "*.pyo", "django-runserver.*.log")


def project_root():
    return Path(__file__).resolve().parents[1]


def default_destination(root):
    return root.parent / "Backup Codigo"


def is_excluded(relative_path):
    parts = relative_path.parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    if len(parts) >= 2 and parts[0] == "app" and parts[1] == "debug":
        return True
    return (
        relative_path.name in EXCLUDED_FILES
        or any(fnmatch.fnmatch(relative_path.name, pattern) for pattern in EXCLUDED_PATTERNS)
    )


def source_files(root):
    for path in root.rglob("*"):
        if path.is_file():
            relative = path.relative_to(root)
            if not is_excluded(relative):
                yield relative, path


def validate_destination(root, destination):
    root = root.resolve()
    destination = destination.resolve()
    if destination == root or root in destination.parents:
        raise ValueError("El respaldo de código debe quedar fuera de la aplicación.")
    return destination


def sync(root, destination):
    destination = validate_destination(root, destination)
    destination.mkdir(parents=True, exist_ok=True)

    expected = set()
    for relative, source in source_files(root):
        expected.add(relative)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if (
            not target.exists()
            or source.stat().st_size != target.stat().st_size
            or source.stat().st_mtime_ns != target.stat().st_mtime_ns
        ):
            shutil.copy2(source, target)

    status_relative = Path("_ULTIMA_SINCRONIZACION.txt")
    expected.add(status_relative)
    for target in sorted(destination.rglob("*"), reverse=True):
        relative = target.relative_to(destination)
        if target.is_file() and relative not in expected:
            target.unlink()
        elif target.is_dir():
            try:
                target.rmdir()
            except OSError:
                pass

    (destination / status_relative).write_text(
        "\n".join(
            (
                "Respaldo único del código del Proyecto Balanza",
                f"Origen: {root.resolve()}",
                f"Actualizado: {datetime.now():%Y-%m-%d %H:%M:%S}",
                "Este directorio se sincroniza; no se generan copias con fecha.",
                "",
            )
        ),
        encoding="utf-8",
    )
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    root = project_root()
    destination = args.destination or default_destination(root)
    print(sync(root, destination))


if __name__ == "__main__":
    main()
