from pathlib import Path

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from app.models import (
    Actividad,
    AuditLog,
    CategoriaResiduos,
    ClaseHorario,
    Destino,
    HistorialRetiro,
    OperationalLock,
    Residuo,
    TipoResiduos,
    Usuarios,
    WeightReading,
)
from app.services.backup_service import create_rolling_backup, create_verified_backup


OPERATIONAL_MODELS = (
    HistorialRetiro,
    Residuo,
    WeightReading,
    ClaseHorario,
    Actividad,
    AuditLog,
    LogEntry,
    Session,
)

LOCK_NAMES = ("unidades", "organico")


class Command(BaseCommand):
    help = (
        "Deja la base sin datos operativos, conservando usuarios, roles, permisos "
        "y configuracion maestra. Siempre crea un respaldo verificado."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirma la limpieza de los datos operativos.",
        )

    def handle(self, *args, **options):
        if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError(
                "La puesta a cero segura solo esta habilitada para la base SQLite del programa."
            )

        counts = {
            model._meta.label: model.objects.count()
            for model in OPERATIONAL_MODELS
        }
        self.stdout.write("Datos operativos encontrados:")
        for label, count in counts.items():
            self.stdout.write(f"  {label}: {count}")

        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "Simulacion: no se modifico la base. Use --confirm para ejecutar."
                )
            )
            return

        try:
            pre_reset_backup = create_verified_backup(
                settings.BACKUP_DIR,
                prefix="antes_limpieza_profesional",
            )
        except (OSError, ValueError) as exc:
            raise CommandError(
                f"No se modifico la base porque fallo el respaldo previo: {exc}"
            ) from exc

        self.stdout.write(f"Respaldo previo verificado: {pre_reset_backup}")

        try:
            with transaction.atomic():
                for model in OPERATIONAL_MODELS:
                    model.objects.all().delete()

                OperationalLock.objects.all().delete()
                OperationalLock.objects.bulk_create(
                    [OperationalLock(name=name, version=0) for name in LOCK_NAMES]
                )
                self._reset_sqlite_sequences()
        except Exception as exc:
            raise CommandError(
                "La limpieza se revirtio por completo debido a un error."
            ) from exc

        self._verify_database_integrity()

        try:
            rolling_backup = create_rolling_backup(settings.BACKUP_DIR)
        except (OSError, ValueError) as exc:
            raise CommandError(
                "La base quedo limpia y el respaldo previo esta seguro, pero no se "
                f"pudo actualizar el respaldo unico: {exc}"
            ) from exc

        preserved = {
            get_user_model()._meta.label: get_user_model().objects.count(),
            Usuarios._meta.label: Usuarios.objects.count(),
            Group._meta.label: Group.objects.count(),
            CategoriaResiduos._meta.label: CategoriaResiduos.objects.count(),
            TipoResiduos._meta.label: TipoResiduos.objects.count(),
            Destino._meta.label: Destino.objects.count(),
        }
        self.stdout.write("Configuracion y usuarios conservados:")
        for label, count in preserved.items():
            self.stdout.write(f"  {label}: {count}")

        total = sum(counts.values())
        self.stdout.write(f"Respaldo unico actualizado: {Path(rolling_backup)}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Puesta a cero completada. Registros operativos eliminados: {total}."
            )
        )

    @staticmethod
    def _reset_sqlite_sequences():
        with connection.cursor() as cursor:
            # Al borrar las secuencias SQLite calcula el próximo ID desde el
            # máximo real de cada tabla. Las tablas conservadas mantienen así
            # su continuidad y las tablas operativas vacías vuelven a ID 1.
            cursor.execute("DELETE FROM sqlite_sequence")

    @staticmethod
    def _verify_database_integrity():
        with connection.cursor() as cursor:
            integrity_result = cursor.execute("PRAGMA integrity_check").fetchone()
            foreign_key_errors = cursor.execute("PRAGMA foreign_key_check").fetchall()

        if not integrity_result or integrity_result[0] != "ok":
            raise CommandError(
                f"La base no supero la comprobacion de integridad: {integrity_result}"
            )
        if foreign_key_errors:
            raise CommandError(
                "La base limpia contiene relaciones invalidas de claves foraneas."
            )
