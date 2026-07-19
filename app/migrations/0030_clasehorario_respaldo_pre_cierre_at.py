from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0029_operationallock"),
    ]

    operations = [
        migrations.AddField(
            model_name="clasehorario",
            name="respaldo_pre_cierre_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text="Último respaldo único generado antes del cierre del taller.",
                null=True,
            ),
        ),
    ]
