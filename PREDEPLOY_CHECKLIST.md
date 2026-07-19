# Checklist previo al despliegue

Este proyecto queda preparado para el paso de despliegue, pero no debe publicarse sin revisar estos puntos.

## 1. Entorno

- Copiar `.env.production.example` a `.env` o ejecutar `.\scripts\setup.ps1 -Production`.
- Cambiar `DJANGO_SECRET_KEY` por una clave larga y privada.
- Cambiar `WEIGHT_API_TOKEN` por un token largo y privado para la balanza.
- Definir `DJANGO_DEBUG=False`.
- Configurar `DJANGO_ALLOWED_HOSTS` con el dominio real.
- Configurar `DJANGO_CSRF_TRUSTED_ORIGINS` con el origen HTTPS real.
- Definir `USE_INSTITUTIONAL_BRAND=True` solo si existe aprobacion formal de uso de marca.
- Mantener `PASSWORD_MAX_AGE_DAYS=120` para la caducidad autorizada del piloto.
- Definir `ENFORCE_INSTITUTIONAL_EMAIL_DOMAIN=True` para limitar usuarios a dominios autorizados.

## 2. Seguridad web

Activar solo cuando el sitio tenga HTTPS correctamente configurado:

```text
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_USE_X_FORWARDED_PROTO=True
DJANGO_TRUSTED_PROXY_IPS=IP_DEL_PROXY_AUTORIZADO
DJANGO_HSTS_SECONDS=31536000
```

## 3. Verificación local

Antes de subir:

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
.\scripts\deploy_check.ps1
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

## 4. Seguridad y auditoria

Generar evidencia:

```powershell
.\scripts\security_check.ps1 -InstallTools
```

Con el servidor levantado, ejecutar DAST:

```powershell
python scripts/serve_app.py --host 0.0.0.0 --port 8000
.\scripts\dast_zap.ps1 -TargetUrl http://host.docker.internal:8000
```

Los reportes quedan fuera del código, en
`..\Archivos personales Proyecto Balanza\Resultados\security\`.

## 5. Respaldo y continuidad

Validar:

```powershell
python manage.py backup_sqlite
python manage.py purge_old_data
python manage.py prune_backups
```

Probar restauracion en una copia del proyecto:

```powershell
python manage.py restore_sqlite "..\Datos Proyecto Balanza\backups\respaldo_base_datos.sqlite3" --confirm
```

## 6. Demo funcional

Validar el flujo completo:

1. Iniciar sesión con un usuario Administrador, Profesor y Estudiante.
2. Registrar un evento desde QR o botón del dashboard.
3. Confirmar el residuo con lectura real de balanza o modo demo.
4. Ver el dashboard actualizado.
5. Registrar un retiro/vaciado.
6. Verificar los XLSX de residuos y retiros en la carpeta automática del taller.
7. Generar backup de base de datos.

## 7. Entrega limpia

No subir ni entregar estos elementos como código fuente:

- `.env`
- `db.sqlite3`
- `venv/`, `.venv/`, `env_win/`
- `logs/`
- `backups/`
- `Backup BD/`
- `Backup Codigo/`
- `outputs/`
- `tmp/`
- `staticfiles/`

En la instalación local, los datos generados deben quedar en `..\Datos Proyecto Balanza\`,
los documentos personales en `..\Archivos personales Proyecto Balanza\` y el espejo único
del código en `..\Backup Codigo\`.
