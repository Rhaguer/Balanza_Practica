from django.db import migrations, models


def normalizar_tipos_taller(apps, schema_editor):
    ClaseHorario = apps.get_model("app", "ClaseHorario")
    ClaseHorario.objects.exclude(
        tipo_taller__in=("organicos", "inorganicos")
    ).update(tipo_taller="organicos")


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0025_seed_tres_tipos_principales"),
    ]

    operations = [
        migrations.RunPython(normalizar_tipos_taller, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="clasehorario",
            name="tipo_taller",
            field=models.CharField(
                choices=[
                    ("organicos", "Orgánicos"),
                    ("inorganicos", "Inorgánicos"),
                ],
                db_index=True,
                default="organicos",
                max_length=40,
            ),
        ),
    ]
