from django.db import migrations


SUBTIPOS_PRINCIPALES = (
    (
        "organico",
        "Orgánico",
        "Residuos biodegradables destinados a compostaje.",
    ),
    (
        "inorganico",
        "Inorgánico",
        "Residuos no biodegradables, reciclables o de disposición final.",
    ),
)


def limitar_subtipos(apps, schema_editor):
    CategoriaResiduos = apps.get_model("app", "CategoriaResiduos")
    TipoResiduos = apps.get_model("app", "TipoResiduos")
    Residuo = apps.get_model("app", "Residuo")

    for tipo_operacional, nombre, descripcion in SUBTIPOS_PRINCIPALES:
        categorias = CategoriaResiduos.objects.filter(
            tipo_operacional=tipo_operacional,
        ).order_by("id_categoria")
        categoria_principal = categorias.first()
        if categoria_principal is None:
            continue

        subtipo_principal, _ = TipoResiduos.objects.update_or_create(
            nombre_residuo=nombre,
            defaults={
                "categoria": categoria_principal,
                "descripcion": descripcion,
            },
        )

        subtipos_adicionales = TipoResiduos.objects.filter(
            categoria__tipo_operacional=tipo_operacional,
        ).exclude(pk=subtipo_principal.pk)
        ids_adicionales = list(
            subtipos_adicionales.values_list("pk", flat=True)
        )
        if ids_adicionales:
            Residuo.objects.filter(subtipo_id__in=ids_adicionales).update(
                subtipo_id=subtipo_principal.pk,
                tipo_id=categoria_principal.pk,
            )
            subtipos_adicionales.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0026_tipos_taller_organicos_inorganicos"),
    ]

    operations = [
        migrations.RunPython(limitar_subtipos, migrations.RunPython.noop),
    ]
