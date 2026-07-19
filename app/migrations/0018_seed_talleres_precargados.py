from datetime import time, timedelta

from django.db import migrations
from django.utils import timezone


TALLERES_PRECARGADOS = (
    ("Taller 1", time(8, 0), time(12, 40)),
    ("Taller 2", time(13, 40), time(18, 20)),
    ("Taller 3", time(18, 30), time(22, 30)),
)


def restaurar_talleres_precargados(apps, schema_editor):
    ClaseHorario = apps.get_model("app", "ClaseHorario")
    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    for dia_semana in range(5):
        fecha = inicio_semana + timedelta(days=dia_semana)
        for nombre, hora_inicio, hora_fin in TALLERES_PRECARGADOS:
            ClaseHorario.objects.update_or_create(
                fecha=fecha,
                profesor="smartadmin",
                asignatura=nombre,
                seccion=nombre,
                defaults={
                    "horario": f"{hora_inicio:%H:%M} - {hora_fin:%H:%M}",
                    "dia_semana": dia_semana,
                    "hora_inicio": hora_inicio,
                    "hora_fin": hora_fin,
                    "archivado": False,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0017_usuarios_password_changed_at"),
    ]

    operations = [
        migrations.RunPython(restaurar_talleres_precargados, migrations.RunPython.noop),
    ]
