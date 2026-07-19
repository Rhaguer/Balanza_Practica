ROL_ADMINISTRADOR = "Administrador"
ROL_PROFESOR = "Profesor"
ROL_ESTUDIANTE = "Estudiante"

ROLES_SISTEMA = [ROL_ADMINISTRADOR, ROL_PROFESOR, ROL_ESTUDIANTE]


def tiene_rol(user, rol):
    return user.is_authenticated and user.groups.filter(name=rol).exists()


def es_administrador(user):
    return user.is_authenticated and (
        user.is_superuser or tiene_rol(user, ROL_ADMINISTRADOR)
    )


def es_profesor(user):
    return tiene_rol(user, ROL_PROFESOR)


def es_estudiante(user):
    return tiene_rol(user, ROL_ESTUDIANTE)


def es_operador(user):
    return es_administrador(user) or es_profesor(user) or es_estudiante(user)


def puede_gestionar_horarios(user):
    return es_administrador(user) or es_profesor(user)


def puede_crear_talleres(user):
    return es_administrador(user) or es_profesor(user)


def puede_ingresar_manual(user):
    return es_administrador(user) or es_profesor(user)


def aplicar_privilegios_por_rol(user, grupo):
    rol = (getattr(grupo, "name", "") or "").strip()
    es_admin = rol == ROL_ADMINISTRADOR

    user.is_staff = es_admin
    user.is_superuser = es_admin
