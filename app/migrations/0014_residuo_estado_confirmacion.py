from django.db import migrations, models


def completar_confirmacion_legacy(apps, schema_editor):
    Residuo = apps.get_model("app", "Residuo")
    Residuo.objects.filter(estado="confirmado", confirmado_at__isnull=True).update(confirmado_at=models.F("hora_escaneo"))


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0013_categoria_tipo_operacional"),
    ]

    operations = [
        migrations.AddField(
            model_name="residuo",
            name="estado",
            field=models.CharField(
                choices=[
                    ("pendiente", "Pendiente"),
                    ("confirmado", "Confirmado"),
                    ("anulado", "Anulado"),
                ],
                db_index=True,
                default="confirmado",
                help_text="Controla si el registro ya fue completado y debe contar en reportes.",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="residuo",
            name="confirmado_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="residuo",
            index=models.Index(fields=["estado", "hora_escaneo"], name="app_residuo_estado_c2a282_idx"),
        ),
        migrations.AddIndex(
            model_name="residuo",
            index=models.Index(fields=["estado", "contenedor_id", "retirado"], name="app_residuo_estado_183fc7_idx"),
        ),
        migrations.RunPython(completar_confirmacion_legacy, migrations.RunPython.noop),
    ]
