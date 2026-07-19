import hashlib
import os
import secrets
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone


def is_sqlite_memory_database():
    database = settings.DATABASES["default"]
    if database["ENGINE"] != "django.db.backends.sqlite3":
        return False

    name = str(database.get("NAME") or "")
    return name == ":memory:" or (
        name.startswith("file:")
        and "mode=memory" in name.lower()
    )


def _sqlite_database_path():
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        raise ImproperlyConfigured("El respaldo verificado solo está disponible para SQLite.")
    return Path(settings.DATABASES["default"]["NAME"]).resolve()


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sqlite_backup(path, require_checksum=False):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f"No se encontró el respaldo: {path}")

    try:
        with closing(sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        raise ValueError("No se pudo validar el respaldo SQLite.") from exc
    if not result or result[0] != "ok":
        raise ValueError(f"El respaldo SQLite no superó la verificación de integridad: {result}")

    checksum_path = path.with_suffix(path.suffix + ".sha256")
    if require_checksum and not checksum_path.is_file():
        raise ValueError("El respaldo no cuenta con archivo de verificación SHA-256.")
    if checksum_path.is_file():
        checksum_parts = checksum_path.read_text(encoding="ascii").split()
        if not checksum_parts:
            raise ValueError("El archivo de verificación SHA-256 está vacío.")
        expected = checksum_parts[0].strip().lower()
        actual = _sha256(path)
        if not secrets.compare_digest(expected, actual):
            raise ValueError("El respaldo no coincide con su verificación SHA-256.")

    return True


def _write_verified_backup(destination):
    source = _sqlite_database_path()
    if not source.is_file():
        raise ValueError(f"No se encontró la base de datos: {source}")

    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    )
    checksum_path = destination.with_suffix(destination.suffix + ".sha256")
    checksum_temporary = checksum_path.with_name(
        f".{checksum_path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    )

    try:
        try:
            with closing(sqlite3.connect(source)) as source_connection:
                with closing(sqlite3.connect(temporary)) as destination_connection:
                    source_connection.backup(destination_connection)
        except sqlite3.Error as exc:
            raise ValueError("No se pudo crear el respaldo SQLite.") from exc
        verify_sqlite_backup(temporary)
        os.replace(temporary, destination)
        checksum = _sha256(destination)
        checksum_temporary.write_text(
            f"{checksum}  {destination.name}\n",
            encoding="ascii",
        )
        os.replace(checksum_temporary, checksum_path)
        verify_sqlite_backup(destination, require_checksum=True)
        return destination
    finally:
        if temporary.exists():
            temporary.unlink()
        if checksum_temporary.exists():
            checksum_temporary.unlink()


def create_verified_backup(output_dir=None, prefix="db_backup"):
    destination_dir = Path(output_dir or settings.BACKUP_DIR)
    if not destination_dir.is_absolute():
        destination_dir = settings.BASE_DIR / destination_dir

    timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S_%f")
    destination = destination_dir / f"{prefix}_{timestamp}.sqlite3"
    return _write_verified_backup(destination)


def create_rolling_backup(output_dir=None, filename=None, cleanup_legacy=True):
    """Actualiza un único respaldo SQLite verificado sin acumular versiones."""
    destination_dir = Path(output_dir or settings.BACKUP_DIR)
    if not destination_dir.is_absolute():
        destination_dir = settings.BASE_DIR / destination_dir

    backup_filename = filename or getattr(
        settings,
        "ROLLING_BACKUP_FILENAME",
        "respaldo_base_datos.sqlite3",
    )
    backup_filename = Path(backup_filename).name
    if not backup_filename.lower().endswith(".sqlite3"):
        backup_filename += ".sqlite3"

    destination = _write_verified_backup(destination_dir / backup_filename)

    if cleanup_legacy:
        for legacy in destination_dir.glob("db_backup_*.sqlite3"):
            if not legacy.is_file() or legacy.resolve() == destination:
                continue
            legacy.unlink()
            legacy_checksum = legacy.with_suffix(legacy.suffix + ".sha256")
            if legacy_checksum.exists():
                legacy_checksum.unlink()

    return destination


def restore_verified_backup(backup_file):
    backup_file = Path(backup_file).resolve()
    verify_sqlite_backup(backup_file, require_checksum=True)

    database = _sqlite_database_path()
    pre_restore = None
    if database.exists():
        pre_restore = create_verified_backup(settings.BACKUP_DIR, prefix="pre_restore")

    temporary = database.with_suffix(database.suffix + ".restore")
    try:
        shutil.copy2(backup_file, temporary)
        verify_sqlite_backup(temporary)
        os.replace(temporary, database)
    finally:
        if temporary.exists():
            temporary.unlink()

    return database, pre_restore
