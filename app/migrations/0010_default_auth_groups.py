from django.db import migrations


def crear_grupos_base(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nombre in ("Administrador", "Profesor"):
        Group.objects.get_or_create(name=nombre)


def eliminar_grupos_base(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=("Administrador", "Profesor")).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0009_secure_user_profiles_and_weightreading"),
    ]

    operations = [
        migrations.RunPython(crear_grupos_base, eliminar_grupos_base),
    ]
