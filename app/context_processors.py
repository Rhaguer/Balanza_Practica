from django.conf import settings

from .roles import es_administrador, es_estudiante, es_operador, es_profesor


def grupos_usuario(request):
    usuario = request.user
    base_context = {
        "use_institutional_brand": settings.USE_INSTITUTIONAL_BRAND,
    }

    if not usuario.is_authenticated:
        return {
            **base_context,
            "es_profesor": False,
            "es_admin": False,
            "es_estudiante": False,
            "es_operador": False,
        }

    return {
        **base_context,
        "es_profesor": es_profesor(usuario),
        "es_admin": es_administrador(usuario),
        "es_estudiante": es_estudiante(usuario),
        "es_operador": es_operador(usuario),
    }
