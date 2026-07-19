from django.db import migrations


TIPOS_RESIDUOS = (
    ("Frutas", "Orgánico", "Orgánico no procesado – frutas/verduras"),
    ("Verduras", "Orgánico", "Orgánico no procesado – frutas/verduras"),
    ("Preparaciones", "Orgánico", "Procesados"),
    ("Genérico", "Inorgánico", "Desecho genérico."),
    ("Aceite", "Líquidos", "Aceite"),
    ("Líquidos", "Líquidos", "Líquido genérico que no es aceite"),
)


def reponer_tipos_residuos(apps, schema_editor):
    CategoriaResiduos = apps.get_model("app", "CategoriaResiduos")
    TipoResiduos = apps.get_model("app", "TipoResiduos")

    for nombre, categoria_nombre, descripcion in TIPOS_RESIDUOS:
        categoria = CategoriaResiduos.objects.filter(
            nombre__iexact=categoria_nombre,
        ).first()
        if categoria is None:
            continue
        TipoResiduos.objects.update_or_create(
            nombre_residuo=nombre,
            defaults={"categoria": categoria, "descripcion": descripcion},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0023_restore_tipos_residuos"),
    ]

    operations = [
        migrations.RunPython(reponer_tipos_residuos, migrations.RunPython.noop),
    ]
