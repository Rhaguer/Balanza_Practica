# Operacion segura, respaldo y continuidad

Este documento define el procedimiento operativo minimo para ejecutar el piloto de Balanza de Mermas en un PC local o en un ambiente publicado.

## Instalacion en cualquier PC

Windows PowerShell:

```powershell
.\scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
python manage.py createsuperuser
python manage.py runserver
```

Linux/macOS:

```bash
bash scripts/setup.sh
source .venv/bin/activate
python manage.py createsuperuser
python manage.py runserver
```

Los scripts crean `.venv`, instalan dependencias, generan `.env` con secretos aleatorios cuando no existe, ejecutan migraciones y validan `manage.py check`.

## Respaldo

Frecuencia recomendada para piloto:

- Antes de cada jornada de uso.
- Al finalizar cada jornada de uso.
- Antes de actualizar codigo o dependencias.
- Antes de restaurar datos.

Comando portable:

```powershell
python manage.py backup_sqlite
```

El respaldo se guarda en `DJANGO_BACKUP_DIR`, por defecto `backups/`, con el nombre fijo
`respaldo_base_datos.sqlite3`. El mismo archivo se actualiza de forma atómica, supera
`PRAGMA integrity_check` y queda acompañado por un `.sha256` para detectar alteraciones.
También se actualiza automáticamente desde 30 segundos antes del fin del taller y de inmediato
después de cada ingreso manual.

## Mantenimiento diario programable

Windows:

```powershell
.\scripts\security_maintenance.ps1
```

Linux/macOS:

```bash
bash scripts/security_maintenance.sh
```

El comando actualiza y verifica el respaldo único y registra la ejecución en `AuditLog`.
Una vez al mes puede incluir la retención de datos con `-PurgeData` en Windows o
`--purge-data` en Linux. Para el piloto debe configurarse en el Programador de tareas de Windows o
cron al cierre de cada jornada.

## Restauracion

1. Detener el servidor Django.
2. Confirmar que el archivo de backup existe.
3. Confirmar que el respaldo y su archivo `.sha256` estén juntos.
4. Ejecutar:

```powershell
python manage.py restore_sqlite backups\respaldo_base_datos.sqlite3 --confirm
```

El comando crea una copia previa `pre_restore_AAAAMMDD_HHMMSS.sqlite3` antes de reemplazar la base actual.

## Poda de respaldos anteriores

`python manage.py prune_backups --execute` queda disponible únicamente para limpiar copias
fechadas antiguas. El flujo normal mantiene un solo respaldo actualizable.

## Retencion de datos

Valores recomendados:

- Datos operacionales: `DATA_RETENTION_DAYS=1095`
- Auditoria: `AUDIT_LOG_RETENTION_DAYS=365`
- Lecturas de balanza: `WEIGHT_READING_RETENTION_DAYS=365`
- Backups: `BACKUP_RETENTION_DAYS=180`

Vista previa:

```powershell
python manage.py purge_old_data
```

Ejecucion real:

```powershell
python manage.py purge_old_data --execute
```

## Continuidad

RTO objetivo para piloto: 4 horas.

RPO objetivo para piloto: ultimo backup de la jornada.

Acciones minimas ante falla del PC:

1. Instalar el proyecto en otro PC con `scripts/setup.ps1` o `scripts/setup.sh`.
2. Copiar el backup mas reciente al nuevo PC.
3. Restaurar con `python manage.py restore_sqlite <backup> --confirm`.
4. Crear o validar usuario administrador.
5. Ejecutar `python manage.py check` y abrir `http://127.0.0.1:8000/`.

## Monitoreo e incidentes

Revisar diariamente:

- `logs/django.log`
- Vista de auditoria en Django Admin: `AuditLog`
- Backups recientes en `backups/`
- Errores del servidor o intentos fallidos de login

Ante un incidente:

1. Detener el servicio si existe riesgo de alteracion de datos.
2. Ejecutar backup inmediato si la base es legible.
3. Guardar copia de `logs/`, `backups/` y `db.sqlite3`.
4. Registrar fecha, usuario afectado, accion sospechosa y evidencia.
5. Cambiar claves comprometidas desde usuario administrador.
6. Restaurar desde backup si hay corrupcion o manipulacion.
7. Documentar causa raiz y accion correctiva antes de reactivar.

## Mantenimiento y soporte

Durante piloto:

- Responsable funcional: encargado del software.
- Responsable tecnico: equipo del proyecto.
- Revisión mensual: dependencias, backups, logs y usuarios activos.
- Revisión antes de cada demostracion: `python manage.py test` y `python manage.py check`.

Para produccion:

- Debe existir responsable formal de operacion.
- Debe definirse mesa de ayuda o canal de soporte.
- Debe acordarse ventana de actualizacion.
- Debe ejecutarse metodologia de desarrollo y seguridad de GST.
