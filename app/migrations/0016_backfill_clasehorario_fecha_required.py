from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def rellenar_fechas_horarios(apps, schema_editor):
    ClaseHorario = apps.get_model("app", "ClaseHorario")
    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    for clase in ClaseHorario.objects.filter(fecha__isnull=True).only("id", "dia_semana"):
        try:
            dia_semana = int(clase.dia_semana)
        except (TypeError, ValueError):
            dia_semana = 0

        dia_semana = min(max(dia_semana, 0), 6)
        fecha = inicio_semana + timedelta(days=dia_semana)
        ClaseHorario.objects.filter(pk=clase.pk, fecha__isnull=True).update(fecha=fecha)


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0015_clasehorario_fecha_archivado"),
    ]

    operations = [
        migrations.RunPython(rellenar_fechas_horarios, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="clasehorario",
            name="fecha",
            field=models.DateField(db_index=True),
        ),
    ]
