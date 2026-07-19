from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0014_residuo_estado_confirmacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="clasehorario",
            name="fecha",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="clasehorario",
            name="archivado",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
