from django.db import models
from django.conf import settings
from django.contrib.auth.models import User # Importamos User para enlazar retiros
from django.utils import timezone
import uuid
from .residue_types import TIPO_OPERACIONAL_CHOICES, TIPO_ORGANICO


ESTADO_RESIDUO_PENDIENTE = "pendiente"
ESTADO_RESIDUO_CONFIRMADO = "confirmado"
ESTADO_RESIDUO_ANULADO = "anulado"

ESTADO_RESIDUO_CHOICES = [
    (ESTADO_RESIDUO_PENDIENTE, "Pendiente"),
    (ESTADO_RESIDUO_CONFIRMADO, "Confirmado"),
    (ESTADO_RESIDUO_ANULADO, "Anulado"),
]


class Residuo(models.Model):

    taller = models.ForeignKey(
        "ClaseHorario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residuos_registrados",
    )

    # El contenedor se asignará dinámicamente según el tipo/subtipo
    contenedor_id = models.CharField(
        max_length=100,
        help_text="Destino del residuo (Compostera o Unidades)",
        null=True,
        blank=True
    )

    # ========================
    # DATOS DE LA CLASE
    # ========================
    seccion = models.CharField(max_length=200)
    profesor = models.CharField(max_length=100)
    asignatura = models.CharField(max_length=100)
    horario = models.CharField(max_length=100)
    numero_clase = models.IntegerField(null=True, blank=True)
    hora_escaneo = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    # ========================
    # NUEVA CATEGORÍA
    # ========================
    tipo = models.ForeignKey(
        'CategoriaResiduos',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='residuos_categoria'
    )

    # ========================
    # NUEVO SUBTIPO
    # ========================
    subtipo = models.ForeignKey(
        'TipoResiduos',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='residuos_tipo'
    )

    # ========================
    # VALORES FÍSICOS
    # ========================
    peso = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    unidad = models.IntegerField(null=True, blank=True)

    # ========================
    # DASHBOARD / RETIRO
    # ========================
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_RESIDUO_CHOICES,
        default=ESTADO_RESIDUO_CONFIRMADO,
        db_index=True,
        help_text="Controla si el registro ya fue completado y debe contar en reportes."
    )
    retirado = models.BooleanField(default=False)
    confirmado_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residuos_creados"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residuos_actualizados"
    )
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    manual_entry = models.BooleanField(default=False, db_index=True)
    manual_reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('asignatura', 'seccion', 'numero_clase')
        indexes = [
            models.Index(fields=["estado", "hora_escaneo"]),
            models.Index(fields=["estado", "contenedor_id", "retirado"]),
            models.Index(fields=["manual_entry", "hora_escaneo"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(peso__isnull=True) | models.Q(peso__gte=0),
                name="residuo_peso_no_negativo",
            ),
            models.CheckConstraint(
                condition=models.Q(unidad__isnull=True) | models.Q(unidad__gte=0),
                name="residuo_unidad_no_negativa",
            ),
            models.CheckConstraint(
                condition=models.Q(peso__isnull=True) | models.Q(unidad__isnull=True),
                name="residuo_una_sola_medicion",
            ),
        ]

    @property
    def esta_confirmado(self):
        return self.estado == ESTADO_RESIDUO_CONFIRMADO

    def __str__(self):
        categoria = self.tipo.nombre if self.tipo else "Sin categoría"
        subtipo = self.subtipo.nombre_residuo if self.subtipo else "Sin subtipo"
        return f"{self.asignatura} | {categoria} | {subtipo} | Contenedor {self.contenedor_id}"

class Destino(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    # antes: CharField con choices
    # ahora: FK a CategoriaResiduos
    categoria = models.ForeignKey(
        "CategoriaResiduos",
        on_delete=models.PROTECT,
        related_name="destinos"
    )

    direccion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["categoria__nombre", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"

class HistorialRetiro(models.Model):
    """Modelo para guardar el respaldo de los vaciados"""
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_retiro = models.DateTimeField(auto_now_add=True)

    contenedor_origen = models.CharField(max_length=50)
    tipo_residuo = models.CharField(max_length=50)

    destino = models.ForeignKey(
        Destino,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="retiros"
    )

    cantidad_peso = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cantidad_unidades = models.IntegerField(default=0)

    detalle = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad_peso__gte=0),
                name="retiro_peso_no_negativo",
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_unidades__gte=0),
                name="retiro_unidades_no_negativas",
            ),
        ]

    def __str__(self):
        return f"Retiro {self.id} → {self.destino.nombre if self.destino else 'Sin destino'}"


class Actividad(models.Model):
    profesor = models.CharField(max_length=100)
    fecha = models.DateField()
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Taller"
        verbose_name_plural = "Talleres"

    def __str__(self):
        return f"{self.nombre} - {self.fecha}"

class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key= True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_usuario",
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=50, null=False, blank=False)
    apellido = models.CharField(max_length=50, null=False, blank=False)
    email = models.CharField(max_length=150, null=False,blank=False, unique= True)
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha del ultimo cambio de clave para controlar caducidad."
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def grupo_principal(self):
        if not self.user_id:
            return "Sin grupo"
        grupo = self.user.groups.first()
        return grupo.name if grupo else "Sin grupo"


class WeightReading(models.Model):
    record_code = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3)
    device_name = models.CharField(max_length=100, blank=True)
    raw_data = models.TextField(blank=True)
    is_stable = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="weight_readings"
    )
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["record_code"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(weight_kg__gte=0),
                name="lectura_peso_no_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.weight_kg} kg - {self.device_name or 'sin dispositivo'}"


class CategoriaResiduos(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo_operacional = models.CharField(
        max_length=20,
        choices=TIPO_OPERACIONAL_CHOICES,
        default=TIPO_ORGANICO,
        db_index=True,
        help_text="Define como se calcula esta categoria en el dashboard."
    )

    def __str__(self):
        return self.nombre

class TipoResiduos(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre_residuo = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    categoria = models.ForeignKey(CategoriaResiduos,on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre_residuo

class ClaseHorario(models.Model):
    TIPO_RECUPERACION_CLASES = "recuperacion_clases"
    TIPO_SESION_EXTRA = "sesion_extra"
    TIPO_ACTIVIDAD_EXTRA_PROGRAMATICA = "actividad_extra_programatica"
    TIPO_NUEVA_ACTIVIDAD = "nueva_actividad"

    TIPO_TALLER_CHOICES = (
        (TIPO_RECUPERACION_CLASES, "Recuperación de clases"),
        (TIPO_SESION_EXTRA, "Sesión extra"),
        (TIPO_ACTIVIDAD_EXTRA_PROGRAMATICA, "Actividad extra programática"),
        (TIPO_NUEVA_ACTIVIDAD, "Nueva actividad"),
    )

    DIA_SEMANA_CHOICES = (
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    )

    seccion = models.CharField(max_length=200)
    profesor = models.CharField(max_length=100)
    asignatura = models.CharField(max_length=100)
    tipo_taller = models.CharField(
        max_length=40,
        choices=TIPO_TALLER_CHOICES,
        default=TIPO_NUEVA_ACTIVIDAD,
        db_index=True,
    )
    horario = models.CharField(max_length=100)
    fecha = models.DateField(db_index=True)
    archivado = models.BooleanField(default=False, db_index=True)
    exportado = models.BooleanField(default=False, db_index=True)
    exportado_at = models.DateTimeField(null=True, blank=True)
    export_error = models.TextField(blank=True, default="")
    export_residuos_path = models.CharField(max_length=500, blank=True)
    export_retiros_path = models.CharField(max_length=500, blank=True)
    export_residuos_descargado_at = models.DateTimeField(null=True, blank=True)
    export_retiros_descargado_at = models.DateTimeField(null=True, blank=True)
    respaldo_pre_cierre_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Último respaldo único generado antes del cierre del taller.",
    )

    dia_semana = models.PositiveSmallIntegerField(choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.asignatura} - {self.seccion} ({self.get_dia_semana_display()})"


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=80)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["action"]),
            models.Index(fields=["model_name", "object_id"]),
        ]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} - {self.action}"


class OperationalLock(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    version = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
