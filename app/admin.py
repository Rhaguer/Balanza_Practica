from django.contrib import admin
from .forms import (
    CategoriaResiduosForm,
    DestinoForm,
    _categorias_residuo_visibles,
)
from .models import (
    Actividad,
    AuditLog,
    CategoriaResiduos,
    ClaseHorario,
    Destino,
    HistorialRetiro,
    Residuo,
    Usuarios,
    WeightReading,
)


@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "email", "grupo_principal", "user")
    search_fields = ("nombre", "apellido", "email", "user__username")


@admin.register(Residuo)
class ResiduoAdmin(admin.ModelAdmin):
    list_display = ("asignatura", "seccion", "tipo", "subtipo", "contenedor_id", "peso", "unidad", "estado", "retirado", "manual_entry", "created_by")
    list_filter = ("estado", "retirado", "manual_entry", "tipo", "subtipo")
    search_fields = ("asignatura", "seccion", "profesor", "contenedor_id", "created_by__username")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tipo":
            kwargs["queryset"] = _categorias_residuo_visibles()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(HistorialRetiro)
class HistorialRetiroAdmin(admin.ModelAdmin):
    list_display = ("fecha_retiro", "usuario", "contenedor_origen", "tipo_residuo", "destino", "cantidad_peso", "cantidad_unidades")
    list_filter = ("tipo_residuo", "destino")


@admin.register(WeightReading)
class WeightReadingAdmin(admin.ModelAdmin):
    list_display = ("created_at", "record_code", "weight_kg", "device_name", "is_stable", "created_by", "source_ip")
    search_fields = ("device_name", "raw_data")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "model_name", "object_id", "user", "ip_address")
    list_filter = ("action", "model_name", "created_at")
    search_fields = ("action", "model_name", "object_id", "user__username", "metadata")
    readonly_fields = ("created_at",)


admin.site.register(Actividad)

@admin.register(CategoriaResiduos)
class CategoriaResiduosAdmin(admin.ModelAdmin):
    form = CategoriaResiduosForm
    list_display = ("nombre", "tipo_operacional", "descripcion")
    list_filter = ("tipo_operacional",)
    search_fields = ("nombre", "descripcion")


@admin.register(ClaseHorario)
class ClaseHorarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "asignatura", "tipo_taller", "seccion", "profesor", "archivado", "exportado", "exportado_at")
    list_filter = ("tipo_taller", "archivado", "exportado", "fecha")
    search_fields = ("asignatura", "seccion", "profesor", "export_error")


@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    form = DestinoForm
    list_display = ("nombre", "categoria", "direccion", "activo")
