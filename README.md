# Proyecto Titulo - Gestion de Residuos

Aplicacion Django para registrar residuos, lecturas de balanza, retiros, usuarios, categorias, destinos y reportes.

## Requisitos

- Python 3.12 o superior
- Git opcional
- Navegador moderno para Web Serial/WebUSB si se conecta una balanza desde el navegador

## Instalación y acceso directo

En Windows haga doble clic una sola vez en `INSTALAR_ACCESO_DIRECTO.bat`. El
instalador prepara el entorno, aplica las migraciones y crea `Balanza de Mermas`
en el escritorio y en el inicio automático de la sesión. Después se usa el
acceso directo, sin abrir VS Code ni PowerShell.

En Linux o macOS:

```bash
bash scripts/install_launcher.sh
```

El iniciador usa Waitress y mantiene supervisados el servidor web, el puente de
la balanza, el cierre/exportación de talleres y el respaldo único del código.
Evita instancias duplicadas y reinicia un componente si se detiene.

Para despliegue en multiples PCs revise `docs/DESPLIEGUE_NACIONAL_BALANZA.md`.

Instalacion manual alternativa:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
notepad .env
python manage.py migrate
python manage.py createsuperuser
python scripts/serve_app.py
```

Abrir:

```text
http://127.0.0.1:8000/
```

## Configuracion

El archivo `.env` permite cambiar configuracion sin tocar codigo. Para uso local copie `.env.example` o ejecute `scripts/setup.ps1`. Para despliegue use `.env.production.example` y cambie todos los valores `cambie-...`.

Las rutas importantes son relativas al proyecto:

```text
DJANGO_DB_NAME=../Datos Proyecto Balanza/db.sqlite3
DJANGO_STATIC_ROOT=../Datos Proyecto Balanza/staticfiles
DJANGO_MEDIA_ROOT=../Datos Proyecto Balanza/media
DJANGO_EXPORT_DIR=../Datos Proyecto Balanza/Excel por Taller
DJANGO_BACKUP_DIR=../Datos Proyecto Balanza/backups
DJANGO_LOG_DIR=../Datos Proyecto Balanza/logs
```

Para produccion:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=una-clave-larga-y-segura
DJANGO_ALLOWED_HOSTS=dominio.com,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://dominio.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_TRUSTED_PROXY_IPS=127.0.0.1,::1
WEIGHT_API_TOKEN=token-largo-y-privado
```

## Balanza externa por API

En Windows, para la HBA-800 con adaptador USB-serial, use el procedimiento de `docs/BALANZA_HBA800_WINDOWS.md`. El modo recomendado es ejecutar `scripts/weight_bridge.ps1` y dejar que la app tome la lectura reciente publicada por el puente.

Endpoint:

```text
POST /api/update_weight/
```

Enviar el token configurado en `.env`:

```text
X-Weight-Token: cambie-este-token-para-la-balanza
```

Ejemplo JSON:

```json
{
  "weight_kg": "12.345",
  "device_name": "balanza-lab",
  "raw_data": "12.345 kg",
  "is_stable": true
}
```

## Seguridad incluida

- Usuarios con roles `Administrador`, `Profesor` y `Estudiante`.
- Contraseñas validadas y hasheadas por Django/Argon2.
- Borrados por POST con CSRF.
- Registro de auditoria para login, usuarios, residuos, retiros, lecturas, reportes y backups.
- Validacion de pesos, unidades y destinos activos.
- Exportación XLSX sin filas ni celdas de datos vacías.
- Backups de SQLite desde el dashboard de administrador.
- Comandos portables de backup, restauracion, retencion y poda de backups.
- Registros de residuos con estado `Pendiente` y `Confirmado` para evitar que datos incompletos afecten el dashboard.
- Lectura de balanza con validacion de estabilidad antes de permitir guardar.
- Detección automática de balanza por puertos Serial, HID y USB disponibles.
- Scripts de SAST, DAST y auditoria de dependencias en `scripts/`.
- Switch `USE_INSTITUTIONAL_BRAND` para desactivar marca si no hay autorizacion formal.

## Flujo de trabajo

1. El administrador crea usuarios, categorias, subtipos y destinos.
2. El profesor o administrador crea horarios/eventos.
3. El estudiante entra al dashboard y usa `Registrar evento`.
4. El sistema carga automaticamente el evento activo segun horario.
5. La balanza USB/API entrega el peso automaticamente.
6. El estudiante selecciona categoria y subtipo del residuo.
7. El dashboard actualiza compostaje o unidades según el tipo operacional.

Después de guardar un residuo, la pantalla permanece abierta y preparada para
el siguiente registro del mismo taller. No es necesario volver al panel entre
registros.

## Capacidades operativas

- Compostera 1: 300 litros.
- Compostera 2: 300 litros.
- Compostera 3: 300 litros, visible pero deshabilitada para nuevos ingresos.
- Almacén de residuos inorgánicos: 1000 unidades.
- Los talleres nuevos se clasifican únicamente como `Orgánicos` o `Inorgánicos`.

## Roles

- `Administrador`: gestiona usuarios, categorias, subtipos, destinos, reportes y backups.
- `Profesor`: gestiona horarios/eventos y puede registrar residuos/retiros.
- `Estudiante`: registra eventos/residuos y puede vaciar contenedores, sin acceso a administracion.

## Categorias y tipo operacional

Cada categoría tiene un campo `tipo_operacional`:

- `Orgánico`: usa peso y se calcula en composteras.
- `Inorgánico`: usa unidades y se calcula en el almacén de unidades.

## Estructura importante del codigo

- `app/roles.py`: roles y permisos del sistema.
- `app/residue_types.py`: tipos operacionales de residuos.
- `app/services/dashboard.py`: calculos del dashboard, capacidades y porcentajes.
- `app/views.py`: vistas HTTP y coordinacion entre formularios, servicios y templates.
- `app/templates/`: pantallas HTML.
- `app/static/js/dashboard.js`: comportamiento del dashboard y modal de retiros.

## Reportes y respaldo

Desde el dashboard, el administrador puede generar reportes XLSX de residuos y
retiros y actualizar el respaldo único de SQLite.

Al terminar un taller se crean automáticamente dos Excel en:
`../Datos Proyecto Balanza/Excel por Taller/<fecha_nombre_taller_id>/`. No se
abre el cuadro de descarga del navegador y cada taller mantiene su propia
carpeta.

El sistema actualiza automáticamente `respaldo_base_datos.sqlite3` desde 30 segundos antes
del fin de cada taller y también inmediatamente después de un ingreso manual. La copia se
reemplaza de forma atómica, por lo que no acumula archivos con fechas distintas.

El código fuente se sincroniza en una sola copia externa:
`../Backup Codigo/`. El vigilante portable actualiza esa copia después de cada
modificación y no crea carpetas fechadas:

```text
python scripts/sync_code_backup.py
python scripts/watch_code_backup.py
```

## Sistemas operativos

- Windows 10/11: aplicación, acceso directo, inicio automático y balanza.
- Linux de escritorio: aplicación e inicio automático; el usuario debe tener
  permiso para el puerto serial/USB.
- macOS: aplicación e inicio automático; la compatibilidad física depende del
  controlador del adaptador USB-serial.
- iPhone/iPad: puede usarse como cliente web en la misma red, pero iOS no
  ejecuta el servidor Python ni conecta directamente esta balanza USB. Para la
  lectura física debe existir un PC Windows, Linux o macOS que actúe como host.

Por consola:

```powershell
python manage.py backup_sqlite
python manage.py restore_sqlite "..\Datos Proyecto Balanza\backups\respaldo_base_datos.sqlite3" --confirm
python manage.py purge_old_data
```

## Seguridad y cumplimiento

Documentacion y evidencia:

- `SECURITY.md`
- `docs/security/COMPLIANCE_MATRIX.md`
- `docs/security/OPERATIONS_SECURITY.md`
- `docs/security/TESTING_AND_AUDIT.md`
- `docs/security/SSO_AND_BRAND.md`
- `docs/security/SECURE_SDLC.md`

Auditoria local:

```powershell
.\scripts\security_check.ps1 -InstallTools
.\scripts\deploy_check.ps1
```

## Antes de desplegar

Revise `PREDEPLOY_CHECKLIST.md`. El proyecto queda preparado para despliegue, pero el paso de publicarlo requiere configurar `.env`, dominio, HTTPS, token de balanza y archivos estaticos.
