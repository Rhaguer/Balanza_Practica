from django.db import migrations


def crear_grupo_estudiante(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Estudiante")


def eliminar_grupo_estudiante(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Estudiante").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0011_auditlog_residuo_created_by_residuo_source_ip_and_more"),
    ]

    operations = [
        migrations.RunPython(crear_grupo_estudiante, eliminar_grupo_estudiante),
    ]
