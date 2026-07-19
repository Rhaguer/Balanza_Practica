TIPO_ORGANICO = "organico"
TIPO_INORGANICO = "inorganico"

TIPO_OPERACIONAL_CHOICES = [
    (TIPO_ORGANICO, "Organico"),
    (TIPO_INORGANICO, "Inorganico"),
]

TIPOS_RESIDUOS_PREDETERMINADOS = (
    ("Orgánico", TIPO_ORGANICO, "Residuos biodegradables destinados a compostaje."),
    ("Inorgánico", TIPO_INORGANICO, "Residuos no biodegradables, reciclables o de disposición final."),
)


def normalizar_texto(value):
    text = (value or "").strip().lower()
    for original, replacement in (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
    ):
        text = text.replace(original, replacement)
    return text


def inferir_tipo_operacional(nombre, default=TIPO_ORGANICO):
    text = normalizar_texto(nombre)
    if "inorg" in text:
        return TIPO_INORGANICO
    if "org" in text or "compost" in text:
        return TIPO_ORGANICO
    return default


def normalizar_tipo_operacional(value):
    text = normalizar_texto(value)
    if text in {TIPO_ORGANICO, TIPO_INORGANICO}:
        return text
    return inferir_tipo_operacional(text, default="")


def tipo_operacional_categoria(categoria):
    tipo = getattr(categoria, "tipo_operacional", "") or ""
    if tipo:
        return normalizar_tipo_operacional(tipo)
    return inferir_tipo_operacional(getattr(categoria, "nombre", ""))


def asegurar_tipos_residuos_predeterminados():
    """Repone los tipos base si una restauración dejó la tabla vacía o incompleta."""
    from .models import CategoriaResiduos, TipoResiduos

    categorias = {
        tipo: CategoriaResiduos.objects.filter(tipo_operacional=tipo)
        .order_by("id_categoria")
        .first()
        for tipo in (TIPO_ORGANICO, TIPO_INORGANICO)
    }

    for nombre, tipo_operacional, descripcion in TIPOS_RESIDUOS_PREDETERMINADOS:
        categoria = categorias.get(tipo_operacional)
        if categoria is None:
            continue
        TipoResiduos.objects.update_or_create(
            nombre_residuo=nombre,
            defaults={
                "categoria": categoria,
                "descripcion": descripcion,
            },
        )
