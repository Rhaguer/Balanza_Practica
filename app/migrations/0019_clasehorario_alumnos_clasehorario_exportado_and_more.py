from django.db import migrations


class Migration(migrations.Migration):
    """Marcador compatible con la variante 0019 entregada previamente.

    Algunas instalaciones ya registraron este nombre. Las columnas compartidas
    se incorporan de forma condicional en la otra rama 0019 para evitar
    duplicados tanto en esas bases como en instalaciones nuevas.
    """

    dependencies = [
        ("app", "0018_seed_talleres_precargados"),
    ]

    operations = []
