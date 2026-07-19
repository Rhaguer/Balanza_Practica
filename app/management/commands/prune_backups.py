from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Elimina backups SQLite mas antiguos que BACKUP_RETENTION_DAYS."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true", help="Elimina archivos encontrados.")
        parser.add_argument("--days", type=int, default=settings.BACKUP_RETENTION_DAYS)
        parser.add_argument("--backup-dir", help="Directorio de backups. Por defecto usa DJANGO_BACKUP_DIR.")

    def handle(self, *args, **options):
        backup_dir = Path(options["backup_dir"]) if options["backup_dir"] else settings.BACKUP_DIR
        if not backup_dir.is_absolute():
            backup_dir = settings.BASE_DIR / backup_dir

        if not backup_dir.exists():
            self.stdout.write(f"No existe el directorio de backups: {backup_dir}")
            return

        cutoff = timezone.now() - timedelta(days=options["days"])
        cutoff_ts = cutoff.timestamp()
        files = [
            path for path in backup_dir.glob("db_backup_*.sqlite3")
            if path.is_file() and path.stat().st_mtime < cutoff_ts
        ]

        for path in files:
            self.stdout.write(str(path))

        if not options["execute"]:
            self.stdout.write(self.style.WARNING(f"Modo simulacion. Archivos encontrados: {len(files)}"))
            return

        for path in files:
            path.unlink()
            checksum = path.with_suffix(path.suffix + ".sha256")
            if checksum.exists():
                checksum.unlink()

        self.stdout.write(self.style.SUCCESS(f"Backups eliminados: {len(files)}"))
