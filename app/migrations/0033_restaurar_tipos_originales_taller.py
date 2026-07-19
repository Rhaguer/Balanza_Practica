from django.db import migrations, models


TIPOS_TALLER = (
    ("recuperacion_clases", "Recuperación de clases"),
    ("sesion_extra", "Sesión extra"),
    ("actividad_extra_programatica", "Actividad extra programática"),
    ("nueva_actividad", "Nueva actividad"),
)


def restaurar_tipos_taller(apps, schema_editor):
    ClaseHorario = apps.get_model("app", "ClaseHorario")
    tipos_por_nombre = {
        "Recuperación de clases": "recuperacion_clases",
        "Sesión extra": "sesion_extra",
        "Actividad extra programática": "actividad_extra_programatica",
        "Nueva actividad": "nueva_actividad",
    }

    for nombre, tipo in tipos_por_nombre.items():
        ClaseHorario.objects.filter(asignatura__iexact=nombre).update(tipo_taller=tipo)

    ClaseHorario.objects.exclude(
        tipo_taller__in=tipos_por_nombre.values()
    ).update(tipo_taller="nueva_actividad")


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0032_data_integrity_constraints"),
    ]

    operations = [
        migrations.RunPython(restaurar_tipos_taller, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="clasehorario",
            name="tipo_taller",
            field=models.CharField(
                choices=TIPOS_TALLER,
                db_index=True,
                default="nueva_actividad",
                max_length=40,
            ),
        ),
    ]
