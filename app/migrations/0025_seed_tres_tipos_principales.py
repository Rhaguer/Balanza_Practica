from django.db import migrations


TIPOS_PRINCIPALES = (
    ("Orgánico", "organico", "Residuos biodegradables destinados a compostaje."),
    ("Inorgánico", "inorganico", "Residuos no biodegradables, reciclables o de disposición final."),
    ("Líquidos", "liquido", "Residuos líquidos, como aceites usados u otros líquidos de proceso."),
)


def crear_tipos_principales(apps, schema_editor):
    CategoriaResiduos = apps.get_model("app", "CategoriaResiduos")
    TipoResiduos = apps.get_model("app", "TipoResiduos")

    for nombre, tipo_operacional, descripcion in TIPOS_PRINCIPALES:
        categoria = CategoriaResiduos.objects.filter(
            tipo_operacional=tipo_operacional,
        ).order_by("id_categoria").first()
        if categoria is None:
            continue
        TipoResiduos.objects.update_or_create(
            nombre_residuo=nombre,
            defaults={"categoria": categoria, "descripcion": descripcion},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0024_reseed_tipos_residuos"),
    ]

    operations = [
        migrations.RunPython(crear_tipos_principales, migrations.RunPython.noop),
    ]
