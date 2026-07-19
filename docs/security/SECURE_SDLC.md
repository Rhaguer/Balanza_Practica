# Estandar minimo de desarrollo seguro

Este proyecto debe mantener los siguientes controles durante piloto y antes de cualquier despliegue.

## Antes de modificar codigo

- Crear una rama de trabajo o copia controlada.
- Revisar alcance del cambio.
- Identificar si afecta autenticacion, autorizacion, datos, reportes o integracion de balanza.
- No subir `.env`, base de datos, logs, backups ni entornos virtuales.

## Durante desarrollo

- Usar validadores Django Forms o validaciones explicitas antes de guardar datos.
- Proteger cambios de estado con POST y CSRF.
- Usar decoradores `login_required`, `admin_required` o validaciones de rol segun corresponda.
- Registrar acciones relevantes con `_audit`.
- Evitar secretos en codigo fuente.
- Mantener rutas configurables por `.env`.
- Evitar dependencias nuevas si no agregan valor claro.

## Antes de entregar

Ejecutar:

```powershell
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py check
python manage.py test
python manage.py backup_sqlite
```

Ejecutar auditoria:

```powershell
.\scripts\security_check.ps1 -InstallTools
```

## Cambios de dependencias

- Editar `requirements.txt`.
- Instalar en un entorno limpio.
- Ejecutar `python -m pip check`.
- Ejecutar `python -m pip_audit -r requirements.txt`.
- Registrar hallazgos o excepciones.

## Criterios de rechazo

No entregar si existe:

- Contrasena o token real en el repositorio.
- Usuario administrador compartido sin control.
- `DEBUG=True` en ambiente publicado.
- `WEIGHT_API_TOKEN` por defecto.
- Backup no probado.
- Tests fallando.
- Hallazgos High sin mitigacion o justificacion.

## Produccion

Si el piloto escala a produccion, el proyecto debe pasar por la metodologia formal de GST. Esta guia no reemplaza controles institucionales, solo deja un piso minimo para el piloto.
