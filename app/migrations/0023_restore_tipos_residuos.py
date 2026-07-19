from django.db import migrations


CATEGORIAS = (
    ("Orgánico", "organico", "Residuos orgánicos y compostables."),
    ("Inorgánico", "inorganico", "Residuos inorgánicos contabilizados por unidad."),
    ("Líquidos", "liquido", "Residuos líquidos medidos por peso."),
)

TIPOS_RESIDUOS = (
    ("Frutas", "Orgánico", "Orgánico no procesado – frutas/verduras"),
    ("Verduras", "Orgánico", "Orgánico no procesado – frutas/verduras"),
    ("Preparaciones", "Orgánico", "Procesados"),
    ("Genérico", "Inorgánico", "Desecho genérico."),
    ("Aceite", "Líquidos", "Aceite"),
    ("Líquidos", "Líquidos", "Líquido genérico que no es aceite"),
)


def restaurar_tipos_residuos(apps, schema_editor):
    CategoriaResiduos = apps.get_model("app", "CategoriaResiduos")
    TipoResiduos = apps.get_model("app", "TipoResiduos")

    categorias = {}
    for nombre, tipo_operacional, descripcion in CATEGORIAS:
        categoria = CategoriaResiduos.objects.filter(nombre__iexact=nombre).first()
        if categoria is None:
            categoria = CategoriaResiduos.objects.create(
                nombre=nombre,
                tipo_operacional=tipo_operacional,
                descripcion=descripcion,
            )
        elif categoria.tipo_operacional != tipo_operacional:
            categoria.tipo_operacional = tipo_operacional
            categoria.save(update_fields=["tipo_operacional"])
        categorias[nombre] = categoria

    for nombre, categoria_nombre, descripcion in TIPOS_RESIDUOS:
        TipoResiduos.objects.update_or_create(
            nombre_residuo=nombre,
            defaults={
                "categoria": categorias[categoria_nombre],
                "descripcion": descripcion,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0022_exportacion_descarga_automatica"),
    ]

    operations = [
        migrations.RunPython(restaurar_tipos_residuos, migrations.RunPython.noop),
    ]
