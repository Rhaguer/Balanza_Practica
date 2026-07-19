from django.db import migrations, models


def crear_bloqueos(apps, schema_editor):
    OperationalLock = apps.get_model("app", "OperationalLock")
    for name in ("unidades", "organico"):
        OperationalLock.objects.get_or_create(name=name)


def enlazar_residuos_con_taller(apps, schema_editor):
    Residuo = apps.get_model("app", "Residuo")
    ClaseHorario = apps.get_model("app", "ClaseHorario")

    for residuo in Residuo.objects.filter(taller__isnull=True).iterator():
        fecha = residuo.hora_escaneo.date() if residuo.hora_escaneo else None
        filtros = {
            "asignatura": residuo.asignatura,
            "seccion": residuo.seccion,
            "profesor": residuo.profesor,
            "horario": residuo.horario,
        }
        if fecha:
            filtros["fecha"] = fecha
        taller = ClaseHorario.objects.filter(**filtros).order_by("id").first()
        if taller:
            Residuo.objects.filter(pk=residuo.pk).update(taller_id=taller.pk)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0028_merge_legacy_0019"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationalLock",
            fields=[
                ("name", models.CharField(max_length=50, primary_key=True, serialize=False)),
                ("version", models.PositiveBigIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name="residuo",
            name="taller",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="residuos_registrados",
                to="app.clasehorario",
            ),
        ),
        migrations.AlterField(
            model_name="residuo",
            name="seccion",
            field=models.CharField(max_length=200),
        ),
        migrations.RunPython(crear_bloqueos, migrations.RunPython.noop),
        migrations.RunPython(enlazar_residuos_con_taller, migrations.RunPython.noop),
    ]
