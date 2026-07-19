from django import forms
from django.conf import settings
from .models import Usuarios, CategoriaResiduos, ClaseHorario, Destino
from django.contrib.auth.models import Group, User
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .residue_types import TIPO_INORGANICO, TIPO_ORGANICO, tipo_operacional_categoria
from .roles import ROLES_SISTEMA, es_administrador


def _categorias_residuo_visibles():
    ids = [
        CategoriaResiduos.objects.filter(tipo_operacional=tipo)
        .order_by("-id_categoria")
        .values_list("id_categoria", flat=True)
        .first()
        for tipo in (TIPO_ORGANICO, TIPO_INORGANICO)
    ]
    return CategoriaResiduos.objects.filter(
        id_categoria__in=[categoria_id for categoria_id in ids if categoria_id]
    ).order_by("id_categoria")


def _nombre_tipo_residuo(categoria):
    return (
        "Inorgánicos"
        if tipo_operacional_categoria(categoria) == TIPO_INORGANICO
        else "Orgánicos"
    )


PASSWORD_REQUIREMENTS_TEXT = (
    # Bandit B105: texto informativo de la política, no una credencial.
    "Entre 8 y 12 caracteres, con mayúscula, minúscula, número y carácter especial "  # nosec B105
    "(por ejemplo: @, #, $, %, &, !), sin espacios."
)

class ClaseHorarioForm(forms.ModelForm):
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        label="Fecha"
    )
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True,
        label="Hora inicio"
    )
    hora_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True,
        label="Hora fin"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["tipo_taller"] = ""

    class Meta:
        model = ClaseHorario
        fields = ['tipo_taller', 'fecha', 'asignatura', 'hora_inicio', 'hora_fin', 'seccion']
        labels = {
            'tipo_taller': 'Tipo de taller',
            'asignatura': 'Nombre del taller',
            'seccion': 'Descripción',
        }
        widgets = {
            'tipo_taller': forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        hora_inicio = cleaned.get("hora_inicio")
        hora_fin = cleaned.get("hora_fin")

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise forms.ValidationError("La hora de fin debe ser posterior a la hora de inicio.")

        return cleaned



class UsuariosForm(forms.ModelForm):
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=ROLES_SISTEMA).order_by("name"),
        required=True,
        label="Rol",
        empty_label="Seleccione un rol",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label="Contraseña",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': 'Entre 8 y 12 caracteres',
            'minlength': '8',
            'maxlength': '12',
        }),
        help_text=PASSWORD_REQUIREMENTS_TEXT,
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': 'Repita la contraseña',
            'minlength': '8',
            'maxlength': '12',
        })
    )

    def __init__(self, *args, **kwargs):
        self.require_password = kwargs.pop("require_password", True)
        self.current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

        if not self.require_password:
            self.fields["password1"].required = False
            self.fields["password2"].required = False
            self.fields["password1"].help_text = (
                "Dejar en blanco para mantener la contraseña actual. "
                f"Si la cambia: {PASSWORD_REQUIREMENTS_TEXT}"
            )
            self.fields["password2"].help_text = "Solo completar si cambiará la contraseña."

        if self.current_user:
            grupo = self.current_user.groups.first()
            if grupo:
                self.fields["grupo"].initial = grupo

    class Meta:
        model = Usuarios
        fields = ['nombre', 'apellido', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if settings.ENFORCE_INSTITUTIONAL_EMAIL_DOMAIN:
            allowed_domains = [domain.lower() for domain in settings.INSTITUTIONAL_EMAIL_DOMAINS]
            domain = email.rsplit("@", 1)[-1] if "@" in email else ""
            if domain not in allowed_domains:
                dominios = ", ".join(allowed_domains)
                raise forms.ValidationError(
                    f"Use un correo institucional autorizado ({dominios})."
                )

        qs_usuarios = Usuarios.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs_usuarios = qs_usuarios.exclude(pk=self.instance.pk)
        if qs_usuarios.exists():
            raise forms.ValidationError("Ya existe un perfil con este correo.")

        qs_users = User.objects.filter(username__iexact=email)
        if self.current_user:
            qs_users = qs_users.exclude(pk=self.current_user.pk)
        if qs_users.exists():
            raise forms.ValidationError("Ya existe un usuario de acceso con este correo.")
        return email

    def _password_validation_user(self, cleaned):
        user = self.current_user or User()
        user.username = cleaned.get("email") or ""
        user.email = cleaned.get("email") or ""
        user.first_name = cleaned.get("nombre") or ""
        user.last_name = cleaned.get("apellido") or ""
        return user

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if self.require_password or password1 or password2:
            if not password1:
                self.add_error("password1", "Ingrese una contraseña.")
            if not password2:
                self.add_error("password2", "Confirme la contraseña.")
            if password1 and password2 and password1 != password2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            if password1 and password2 and password1 == password2:
                try:
                    password_validation.validate_password(
                        password1,
                        self._password_validation_user(cleaned)
                    )
                except ValidationError as error:
                    self.add_error("password1", error)

        return cleaned

class CategoriaResiduosForm(forms.ModelForm):  #  con mayúscula inicial
    class Meta:
        model = CategoriaResiduos
        fields = ['nombre', 'tipo_operacional', 'descripcion']
        labels = {
            'tipo_operacional': 'Tipo de residuo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_operacional': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo_operacional"].choices = (
            (TIPO_ORGANICO, "Orgánico"),
            (TIPO_INORGANICO, "Inorgánico"),
        )

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        qs = CategoriaResiduos.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una categoría con ese nombre.")
        return nombre

class DestinoForm(forms.ModelForm):
    class Meta:
        model = Destino
        fields = ["nombre", "categoria", "direccion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = _categorias_residuo_visibles()
        self.fields["categoria"].label_from_instance = _nombre_tipo_residuo

    def clean_nombre(self):
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        qs = Destino.objects.filter(nombre__iexact=nombre)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un destino con ese nombre.")
        return nombre


MEDICION_PESO_KG = "peso_kg"
MEDICION_UNIDADES = "unidades"
MEDICION_CHOICES = (
    (MEDICION_PESO_KG, "Peso (kg)"),
    (MEDICION_UNIDADES, "Cantidad (unidades)"),
)


class CategoriaMedicionSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-tipo-operacional"] = instance.tipo_operacional
        return option


class ManualResiduoOlvidoForm(forms.Form):
    fecha = forms.DateField(
        label="Fecha del taller",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        required=True,
    )
    taller = forms.ModelChoiceField(
        label="Taller",
        queryset=ClaseHorario.objects.none(),
        empty_label="Seleccione un taller",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )
    categoria = forms.ModelChoiceField(
        label="Tipo de residuo",
        queryset=CategoriaResiduos.objects.order_by("id_categoria"),
        empty_label="Seleccione un tipo de residuo",
        widget=CategoriaMedicionSelect(attrs={"class": "form-select"}),
        required=True,
    )
    tipo_medicion = forms.ChoiceField(
        label="Tipo de medición",
        choices=(("", "Seleccione una medición"), *MEDICION_CHOICES),
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )
    cantidad = forms.DecimalField(
        label="Valor de la medición",
        min_value=0,
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.001",
            "min": "0",
            "inputmode": "decimal",
        }),
        required=True,
    )
    motivo = forms.CharField(
        label="Motivo",
        max_length=255,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        talleres = ClaseHorario.objects.exclude(profesor="smartadmin").order_by(
            "-fecha",
            "-hora_inicio",
            "asignatura",
        )
        if user is not None and not es_administrador(user):
            talleres = talleres.filter(profesor=user.username)

        self.fields["taller"].queryset = talleres
        self.fields["taller"].label_from_instance = self._label_taller
        self.fields["categoria"].queryset = _categorias_residuo_visibles()
        self.fields["categoria"].label_from_instance = _nombre_tipo_residuo

    @staticmethod
    def _label_taller(taller):
        return (
            f"{taller.fecha:%d-%m-%Y} - {taller.asignatura} "
            f"({taller.seccion}) {taller.hora_inicio:%H:%M}-{taller.hora_fin:%H:%M}"
        )

    def clean_motivo(self):
        motivo = (self.cleaned_data.get("motivo") or "").strip()
        if not motivo:
            raise forms.ValidationError("El motivo del ingreso es obligatorio.")
        return motivo

    def clean(self):
        cleaned = super().clean()
        fecha = cleaned.get("fecha")
        taller = cleaned.get("taller")
        categoria = cleaned.get("categoria")
        tipo_medicion = cleaned.get("tipo_medicion")
        cantidad = cleaned.get("cantidad")

        if taller and fecha and taller.fecha != fecha:
            self.add_error("fecha", "La fecha debe coincidir con el taller seleccionado.")

        if cantidad is not None and cantidad <= 0:
            self.add_error("cantidad", "La cantidad debe ser mayor a 0.")

        if categoria:
            tipo_operacional = tipo_operacional_categoria(categoria)
            medicion_esperada = (
                MEDICION_UNIDADES if tipo_operacional == TIPO_INORGANICO else MEDICION_PESO_KG
            )
            if tipo_medicion and tipo_medicion != medicion_esperada:
                self.add_error(
                    "tipo_medicion",
                    "La medición seleccionada no corresponde al tipo de residuo.",
                )
            if (
                tipo_medicion == MEDICION_UNIDADES
                and cantidad is not None
                and cantidad != cantidad.to_integral_value()
            ):
                self.add_error("cantidad", "Los residuos inorgánicos deben ingresarse en unidades enteras.")
            if tipo_medicion == MEDICION_UNIDADES and cantidad is not None and cantidad > 1000:
                self.add_error("cantidad", "El máximo permitido es de 1000 unidades.")

        return cleaned
