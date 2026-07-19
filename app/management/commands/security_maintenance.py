from django.core.management import call_command
from django.core.management.base import BaseCommand

from app.models import AuditLog


class Command(BaseCommand):
    help = "Ejecuta respaldo verificado, poda de respaldos y retención opcional."

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge-data",
            action="store_true",
            help="Aplica también la política de retención de datos.",
        )

    def handle(self, *args, **options):
        call_command("backup_sqlite")
        call_command("prune_backups", execute=True)
        if options["purge_data"]:
            call_command("purge_old_data", execute=True)

        AuditLog.objects.create(
            action="security_maintenance_completed",
            model_name="system",
            metadata={"purge_data": bool(options["purge_data"])},
        )
        self.stdout.write(self.style.SUCCESS("Mantenimiento de seguridad completado."))
