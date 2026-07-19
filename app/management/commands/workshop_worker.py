import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from app.views import _cerrar_talleres_terminados


class Command(BaseCommand):
    help = (
        "Cierra talleres terminados y guarda sus Excel directamente en la "
        "carpeta configurada, sin depender del navegador."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Ejecuta una sola revisión y termina.",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=settings.WORKSHOP_WORKER_INTERVAL_SECONDS,
            help="Segundos entre revisiones (por defecto: settings).",
        )

    def handle(self, *args, **options):
        interval = max(options["interval"], 1)
        once = options["once"]
        self.stdout.write(
            f"Vigilancia de talleres activa; revisión cada {interval} segundos."
        )

        while True:
            close_old_connections()
            try:
                cerrados = _cerrar_talleres_terminados(None)
                if cerrados:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{cerrados} taller(es) cerrado(s) y exportado(s)."
                        )
                    )
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"Error revisando talleres: {exc}")
                )
            finally:
                close_old_connections()

            if once:
                return
            time.sleep(interval)
