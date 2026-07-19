from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0031_solo_organicos_inorganicos"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="residuo",
            constraint=models.CheckConstraint(
                condition=models.Q(("peso__isnull", True), ("peso__gte", 0), _connector="OR"),
                name="residuo_peso_no_negativo",
            ),
        ),
        migrations.AddConstraint(
            model_name="residuo",
            constraint=models.CheckConstraint(
                condition=models.Q(("unidad__isnull", True), ("unidad__gte", 0), _connector="OR"),
                name="residuo_unidad_no_negativa",
            ),
        ),
        migrations.AddConstraint(
            model_name="residuo",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("peso__isnull", True),
                    ("unidad__isnull", True),
                    _connector="OR",
                ),
                name="residuo_una_sola_medicion",
            ),
        ),
        migrations.AddConstraint(
            model_name="historialretiro",
            constraint=models.CheckConstraint(
                condition=models.Q(("cantidad_peso__gte", 0)),
                name="retiro_peso_no_negativo",
            ),
        ),
        migrations.AddConstraint(
            model_name="historialretiro",
            constraint=models.CheckConstraint(
                condition=models.Q(("cantidad_unidades__gte", 0)),
                name="retiro_unidades_no_negativas",
            ),
        ),
        migrations.AddConstraint(
            model_name="weightreading",
            constraint=models.CheckConstraint(
                condition=models.Q(("weight_kg__gte", 0)),
                name="lectura_peso_no_negativo",
            ),
        ),
    ]
