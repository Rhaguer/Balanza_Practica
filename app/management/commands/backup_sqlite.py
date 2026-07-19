from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from app.models import AuditLog
from app.services.backup_service import create_rolling_backup


class Command(BaseCommand):
    help = "Crea o actualiza el único respaldo verificado de la base SQLite."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            help="Directorio destino. Por defecto usa DJANGO_BACKUP_DIR.",
        )

    def handle(self, *args, **options):
        engine = settings.DATABASES["default"]["ENGINE"]
        if engine != "django.db.backends.sqlite3":
            raise CommandError("backup_sqlite solo esta disponible para SQLite.")

        output_dir = Path(options["output_dir"]) if options["output_dir"] else settings.BACKUP_DIR
        try:
            destination = create_rolling_backup(output_dir)
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        AuditLog.objects.create(
            action="database_rolling_backup_updated",
            model_name="database",
            metadata={
                "path": str(destination),
                "verified": True,
                "modo": "unico_actualizable",
                "motivo": "comando",
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Respaldo único actualizado: {destination}"))
