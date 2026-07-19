from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from app.services.backup_service import restore_verified_backup


class Command(BaseCommand):
    help = "Restaura la base SQLite desde un backup, creando una copia previa."

    def add_arguments(self, parser):
        parser.add_argument("backup_file", help="Ruta al archivo .sqlite3 de respaldo.")
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirma el reemplazo de la base actual.",
        )

    def handle(self, *args, **options):
        if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("restore_sqlite solo esta disponible para SQLite.")

        if not options["confirm"]:
            raise CommandError("Use --confirm para restaurar. Revise que la app este detenida.")

        backup_file = Path(options["backup_file"])
        if not backup_file.is_absolute():
            backup_file = settings.BASE_DIR / backup_file
        if not backup_file.exists():
            raise CommandError(f"No se encontro el backup: {backup_file}")

        try:
            database, pre_restore = restore_verified_backup(backup_file)
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        if pre_restore:
            self.stdout.write(f"Copia previa verificada creada: {pre_restore}")
        self.stdout.write(self.style.SUCCESS(f"Base restaurada desde: {backup_file}"))
