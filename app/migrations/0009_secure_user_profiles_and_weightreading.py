from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def vincular_usuarios(apps, schema_editor):
    UsuarioPerfil = apps.get_model("app", "Usuarios")
    User = apps.get_model("auth", "User")

    for perfil in UsuarioPerfil.objects.all():
        email = (perfil.email or "").strip().lower()
        if not email:
            continue

        user = User.objects.filter(username__iexact=email).first()
        if user is None:
            user = User.objects.filter(email__iexact=email, is_superuser=False).first()

        password_plana = getattr(perfil, "contraseña", "") or ""

        if user is None:
            user = User(
                username=email,
                email=email,
                first_name=perfil.nombre,
                last_name=perfil.apellido,
                is_active=True,
                is_staff=False,
                is_superuser=False,
                password=make_password(password_plana) if password_plana else make_password(None),
            )
        else:
            user.username = email
            user.email = email
            user.first_name = perfil.nombre
            user.last_name = perfil.apellido
            if password_plana:
                user.password = make_password(password_plana)

        user.save()
        perfil.user_id = user.id
        perfil.save(update_fields=["user"])


def desvincular_usuarios(apps, schema_editor):
    UsuarioPerfil = apps.get_model("app", "Usuarios")
    UsuarioPerfil.objects.update(user=None)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("app", "0008_alter_destino_categoria"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuarios",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="perfil_usuario",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(vincular_usuarios, desvincular_usuarios),
        migrations.RemoveField(
            model_name="usuarios",
            name="contraseña",
        ),
        migrations.CreateModel(
            name="WeightReading",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("weight_kg", models.DecimalField(decimal_places=3, max_digits=8)),
                ("device_name", models.CharField(blank=True, max_length=100)),
                ("raw_data", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
