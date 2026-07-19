from django.db import migrations, models


def eliminar_maestros_liquidos(apps, schema_editor):
    CategoriaResiduos = apps.get_model("app", "CategoriaResiduos")
    Destino = apps.get_model("app", "Destino")
    TipoResiduos = apps.get_model("app", "TipoResiduos")

    categorias_liquidas = CategoriaResiduos.objects.filter(
        tipo_operacional="liquido",
    )
    Destino.objects.filter(categoria__in=categorias_liquidas).delete()
    TipoResiduos.objects.filter(categoria__in=categorias_liquidas).delete()
    categorias_liquidas.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0030_clasehorario_respaldo_pre_cierre_at"),
    ]

    operations = [
        migrations.RunPython(
            eliminar_maestros_liquidos,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="categoriaresiduos",
            name="tipo_operacional",
            field=models.CharField(
                choices=[
                    ("organico", "Organico"),
                    ("inorganico", "Inorganico"),
                ],
                db_index=True,
                default="organico",
                help_text="Define como se calcula esta categoria en el dashboard.",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="residuo",
            name="contenedor_id",
            field=models.CharField(
                blank=True,
                help_text="Destino del residuo (Compostera o Unidades)",
                max_length=100,
                null=True,
            ),
        ),
    ]
