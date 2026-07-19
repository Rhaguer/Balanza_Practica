from django.db import migrations, models


def inferir_tipo(nombre):
    text = (nombre or "").strip().lower()
    for original, replacement in (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
    ):
        text = text.replace(original, replacement)

    if "inorg" in text:
        return "inorganico"
    if "liq" in text:
        return "liquido"
    if "org" in text or "compost" in text:
        return "organico"
    return "organico"


def clasificar_categorias(apps, schema_editor):
    CategoriaResiduos = apps.get_model("app", "CategoriaResiduos")
    for categoria in CategoriaResiduos.objects.all():
        categoria.tipo_operacional = inferir_tipo(categoria.nombre)
        categoria.save(update_fields=["tipo_operacional"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0012_add_estudiante_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoriaresiduos",
            name="tipo_operacional",
            field=models.CharField(
                choices=[
                    ("organico", "Organico"),
                    ("inorganico", "Inorganico"),
                    ("liquido", "Liquido"),
                ],
                db_index=True,
                default="organico",
                help_text="Define como se calcula esta categoria en el dashboard.",
                max_length=20,
            ),
        ),
        migrations.RunPython(clasificar_categorias, migrations.RunPython.noop),
    ]
