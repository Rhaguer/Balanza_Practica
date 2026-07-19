from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.models import (
    ESTADO_RESIDUO_ANULADO,
    AuditLog,
    HistorialRetiro,
    Residuo,
    WeightReading,
)


class Command(BaseCommand):
    help = "Aplica la politica de retencion configurada para datos operativos y auditoria."

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true", help="Elimina los registros encontrados.")
        parser.add_argument("--data-days", type=int, default=settings.DATA_RETENTION_DAYS)
        parser.add_argument("--audit-days", type=int, default=settings.AUDIT_LOG_RETENTION_DAYS)
        parser.add_argument("--weight-days", type=int, default=settings.WEIGHT_READING_RETENTION_DAYS)

    def handle(self, *args, **options):
        now = timezone.now()
        data_cutoff = now - timedelta(days=options["data_days"])
        audit_cutoff = now - timedelta(days=options["audit_days"])
        weight_cutoff = now - timedelta(days=options["weight_days"])

        querysets = {
            "audit_logs": AuditLog.objects.filter(created_at__lt=audit_cutoff),
            "weight_readings": WeightReading.objects.filter(created_at__lt=weight_cutoff),
            "residuos_anulados": Residuo.objects.filter(
                estado=ESTADO_RESIDUO_ANULADO,
                hora_escaneo__lt=data_cutoff,
            ),
            "retiros": HistorialRetiro.objects.filter(fecha_retiro__lt=data_cutoff),
        }

        counts = {name: qs.count() for name, qs in querysets.items()}
        for name, count in counts.items():
            self.stdout.write(f"{name}: {count} registro(s)")

        if not options["execute"]:
            self.stdout.write(self.style.WARNING("Modo simulacion. Use --execute para eliminar."))
            return

        with transaction.atomic():
            for qs in querysets.values():
                qs.delete()

        total = sum(counts.values())
        self.stdout.write(self.style.SUCCESS(f"Retencion aplicada. Eliminados: {total}"))
