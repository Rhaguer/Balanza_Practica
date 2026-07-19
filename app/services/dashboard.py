import json
from decimal import Decimal, InvalidOperation

from django.db.models import Sum

from app.models import (
    ESTADO_RESIDUO_CONFIRMADO,
    ESTADO_RESIDUO_PENDIENTE,
    AuditLog,
    CategoriaResiduos,
    Destino,
    Residuo,
    TipoResiduos,
    WeightReading,
)
from app.residue_types import TIPO_INORGANICO, TIPO_ORGANICO
from app.roles import es_administrador


CONTENEDORES_OPERATIVOS = [
    "Compostera 1",
    "Compostera 2",
]

CONTENEDORES_ORDENADOS = [
    *CONTENEDORES_OPERATIVOS,
    "Compostera 3",
]

CONTENEDOR_CONFIG = {
    "Compostera 1": {"nombre": "Contenedor (C1)", "volumen_total": 300.0, "habilitado": True},
    "Compostera 2": {"nombre": "Contenedor (C2)", "volumen_total": 300.0, "habilitado": True},
    "Compostera 3": {"nombre": "Contenedor (C3)", "volumen_total": 300.0, "habilitado": False},
}

LIMITE_UNIDADES_GLOBAL = 1000
DENSIDAD_ESTIMADA_KG_L = 0.25
CAPACIDAD_TANQUE_LIQUIDOS = 200.0
TIPO_LIQUIDO_LEGACY = "liquido"
GRAFICO_LIQUIDOS_HABILITADO = False
DASHBOARD_CLEARED_ACTION = "dashboard_cleared"


def _residuos_confirmados():
    return Residuo.objects.filter(estado=ESTADO_RESIDUO_CONFIRMADO)


def _residuos_confirmados_activos():
    return _residuos_confirmados().filter(retirado=False)


def _ultima_limpieza_panel():
    return (
        AuditLog.objects
        .filter(action=DASHBOARD_CLEARED_ACTION)
        .order_by("-created_at")
        .first()
    )


def obtener_proximo_contenedor_disponible(peso_nuevo_kg):
    asignaciones = distribuir_peso_organico(peso_nuevo_kg)
    if not asignaciones:
        return None
    return asignaciones[0]["contenedor"]


def distribuir_peso_organico(peso_nuevo_kg, residuo_excluido_id=None):
    """Distribuye un ingreso en C1 y luego C2 sin superar los 300 L de cada una."""
    try:
        peso_pendiente = Decimal(str(peso_nuevo_kg or 0))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if peso_pendiente <= 0:
        return []

    densidad = Decimal(str(DENSIDAD_ESTIMADA_KG_L))
    if densidad <= 0:
        return None

    asignaciones = []

    for contenedor in CONTENEDORES_OPERATIVOS:
        config = CONTENEDOR_CONFIG[contenedor]
        capacidad_peso = Decimal(str(config["volumen_total"])) * densidad
        residuos = _residuos_confirmados().filter(
            contenedor_id=contenedor,
            retirado=False,
        )
        if residuo_excluido_id:
            residuos = residuos.exclude(pk=residuo_excluido_id)
        peso_acumulado = residuos.aggregate(total=Sum("peso"))["total"] or Decimal("0")
        disponible = max(capacidad_peso - Decimal(peso_acumulado), Decimal("0"))
        asignado = min(peso_pendiente, disponible)
        if asignado > 0:
            asignaciones.append({
                "contenedor": contenedor,
                "peso_kg": asignado.quantize(Decimal("0.001")),
            })
            peso_pendiente -= asignado
        if peso_pendiente <= 0:
            return asignaciones

    return None


def _datos_compostaje():
    datos_peso = []

    for device_name, config in CONTENEDOR_CONFIG.items():
        volumen_total = config["volumen_total"]
        peso_total = float(
            _residuos_confirmados().filter(
                contenedor_id=device_name,
                retirado=False,
                tipo__tipo_operacional=TIPO_ORGANICO,
            )
            .aggregate(total=Sum("peso"))["total"] or 0.0
        )

        volumen_actual = peso_total / DENSIDAD_ESTIMADA_KG_L if DENSIDAD_ESTIMADA_KG_L else 0
        porcentaje = (volumen_actual / volumen_total * 100) if volumen_total > 0 else 0

        datos_peso.append({
            "nombre": config["nombre"],
            "device_name": device_name,
            "habilitado": bool(config.get("habilitado", True)),
            "peso_actual": round(peso_total, 2),
            "volumen_total": volumen_total,
            "volumen_actual": round(volumen_actual, 2),
            "porcentaje": round(porcentaje, 1),
        })

    return datos_peso


def _datos_unidades():
    total_unidades = (
        _residuos_confirmados().filter(
            retirado=False,
            tipo__tipo_operacional=TIPO_INORGANICO,
        )
        .aggregate(total=Sum("unidad"))["total"] or 0
    )

    unidades_qs = (
        _residuos_confirmados().filter(
            retirado=False,
            tipo__tipo_operacional=TIPO_INORGANICO,
        )
        .values("subtipo__nombre_residuo")
        .annotate(cantidad=Sum("unidad"))
    )

    tipos_unidades_map = {
        item["subtipo__nombre_residuo"]: item["cantidad"]
        for item in unidades_qs if item["subtipo__nombre_residuo"]
    }

    porcentaje_global = (
        total_unidades / LIMITE_UNIDADES_GLOBAL * 100
        if LIMITE_UNIDADES_GLOBAL else 0
    )

    return {
        "total": total_unidades,
        "limite_total": LIMITE_UNIDADES_GLOBAL,
        "porcentaje_global": round(porcentaje_global, 1),
        "tipos": tipos_unidades_map,
    }


def obtener_datos_unidades():
    return _datos_unidades()


def _datos_liquidos():
    """Conserva el cálculo histórico del tanque sin reactivar su operación."""
    residuos_liquidos = _residuos_confirmados().filter(
        retirado=False,
        tipo__tipo_operacional=TIPO_LIQUIDO_LEGACY,
    )
    total_liquidos_litros = float(
        residuos_liquidos.aggregate(total=Sum("peso"))["total"] or 0.0
    )
    liquidos_qs = (
        residuos_liquidos
        .values("subtipo__nombre_residuo")
        .annotate(cantidad=Sum("peso"))
    )
    tipos_liquidos_map = {
        item["subtipo__nombre_residuo"]: float(item["cantidad"] or 0)
        for item in liquidos_qs
        if item["subtipo__nombre_residuo"]
    }
    porcentaje_liquidos = (
        total_liquidos_litros / CAPACIDAD_TANQUE_LIQUIDOS * 100
        if CAPACIDAD_TANQUE_LIQUIDOS
        else 0
    )

    return {
        "habilitado": GRAFICO_LIQUIDOS_HABILITADO,
        "total_litros": round(total_liquidos_litros, 2),
        "capacidad": CAPACIDAD_TANQUE_LIQUIDOS,
        "porcentaje": round(porcentaje_liquidos, 1),
        "tipos": tipos_liquidos_map,
    }


def _alertas_operativas(datos_peso, datos_unidades, datos_liquidos, pendientes):
    alertas = []
    composteras_operativas = [
        contenedor for contenedor in datos_peso if contenedor.get("habilitado", True)
    ]

    if composteras_operativas and all(
        contenedor["porcentaje"] >= 100 for contenedor in composteras_operativas
    ):
        alertas.append({
            "nivel": "critico",
            "titulo": "Composteras operativas completas",
            "detalle": "Compostera 1 y Compostera 2 alcanzaron su capacidad. Compostera 3 no acepta nuevos ingresos.",
        })

    for contenedor in datos_peso:
        if not contenedor.get("habilitado", True):
            continue
        porcentaje = contenedor["porcentaje"]
        if porcentaje >= 90:
            alertas.append({
                "nivel": "critico",
                "titulo": f"{contenedor['device_name']} casi llena",
                "detalle": f"{porcentaje:.1f}% de ocupación estimada.",
            })
        elif porcentaje >= 75:
            alertas.append({
                "nivel": "advertencia",
                "titulo": f"{contenedor['device_name']} requiere seguimiento",
                "detalle": f"{porcentaje:.1f}% de ocupación estimada.",
            })

    if datos_unidades["porcentaje_global"] >= 85:
        alertas.append({
            "nivel": "advertencia",
            "titulo": "Almacén de unidades alto",
            "detalle": f"{datos_unidades['total']} de {datos_unidades['limite_total']} unidades registradas.",
        })

    if (
        datos_liquidos["habilitado"]
        and datos_liquidos["porcentaje"] >= 85
    ):
        alertas.append({
            "nivel": "advertencia",
            "titulo": "Tanque de líquidos alto",
            "detalle": (
                f"{datos_liquidos['total_litros']} L de "
                f"{datos_liquidos['capacidad']} L."
            ),
        })

    if pendientes:
        alertas.append({
            "nivel": "info",
            "titulo": "Registros pendientes",
            "detalle": f"{pendientes} registro(s) iniciado(s) aún no fueron completados.",
        })

    return alertas


def crear_dashboard_context(user):
    datos_peso = _datos_compostaje()
    datos_unidades = _datos_unidades()
    datos_liquidos = _datos_liquidos()
    residuos_pendientes_qs = (
        Residuo.objects
        .filter(estado=ESTADO_RESIDUO_PENDIENTE)
        .select_related("taller", "tipo", "subtipo", "created_by")
        .order_by("-created_at", "-hora_escaneo")
    )
    pendientes = residuos_pendientes_qs.count()
    detalle_pendientes = []
    usuario_es_admin = es_administrador(user)
    for residuo in residuos_pendientes_qs:
        faltantes = []
        if residuo.tipo_id is None:
            faltantes.append("seleccionar el tipo de residuo")
        tipo_operacional = getattr(residuo.tipo, "tipo_operacional", "")
        if tipo_operacional == TIPO_ORGANICO and not residuo.peso:
            faltantes.append("registrar el peso")
        elif tipo_operacional == TIPO_INORGANICO and not residuo.unidad:
            faltantes.append("registrar las unidades")
        elif residuo.tipo_id is None:
            faltantes.append("ingresar la medición correspondiente")

        puede_gestionar = usuario_es_admin or (
            residuo.created_by_id is not None and residuo.created_by_id == user.id
        )
        detalle_pendientes.append({
            "residuo": residuo,
            "puede_gestionar": puede_gestionar,
            "accion_requerida": (
                "Falta " + ", ".join(faltantes) + "."
                if faltantes
                else "Revise los datos y termine la confirmación del registro."
            ),
        })

    categorias_bd = CategoriaResiduos.objects.all().values(
        "id_categoria",
        "nombre",
        "tipo_operacional",
    )
    tipos_bd = TipoResiduos.objects.values("id_tipo", "nombre_residuo", "categoria_id")
    destinos_bd = (
        Destino.objects
        .filter(activo=True)
        .select_related("categoria")
        .values("id", "nombre", "categoria_id", "categoria__nombre")
    )

    ultimos_residuos = (
        _residuos_confirmados_activos()
        .select_related("tipo", "subtipo", "created_by")
        .order_by("-confirmado_at", "-hora_escaneo")[:5]
    )
    ultimas_lecturas_qs = WeightReading.objects.order_by("-created_at")
    ultima_limpieza = _ultima_limpieza_panel()
    if ultima_limpieza:
        ultimas_lecturas_qs = ultimas_lecturas_qs.filter(created_at__gt=ultima_limpieza.created_at)
    ultimas_lecturas = ultimas_lecturas_qs[:5]

    return {
        "datos_peso": datos_peso,
        "datos_unidades": datos_unidades,
        "datos_liquidos": datos_liquidos,
        "total_peso_organico": round(sum(item["peso_actual"] for item in datos_peso), 2),
        "TITULO_DASHBOARD": "Panel de Sostenibilidad",
        "categorias_list": json.dumps(list(categorias_bd)),
        "tipos_list": json.dumps(list(tipos_bd)),
        "destinos_list": json.dumps(list(destinos_bd)),
        "destinos_bd": destinos_bd,
        "alertas_operativas": _alertas_operativas(
            datos_peso,
            datos_unidades,
            datos_liquidos,
            pendientes,
        ),
        "residuos_pendientes": pendientes,
        "detalle_pendientes": detalle_pendientes,
        "total_residuos_confirmados": _residuos_confirmados_activos().count(),
        "ultimos_residuos": ultimos_residuos,
        "ultimas_lecturas": ultimas_lecturas,
        "usuario_actual": user.username if user.is_authenticated else "Invitado",
    }
