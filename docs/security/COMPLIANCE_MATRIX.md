# Matriz de cumplimiento del informe de riesgos

Fecha de actualizacion: 2026-07-10

Esta matriz resume como el proyecto responde a los riesgos RIE-001 a RIE-009 del informe de ciberseguridad del software Balanza de Mermas.

| Riesgo | Control implementado | Evidencia en el proyecto | Estado |
| --- | --- | --- | --- |
| RIE-001: contrasenas en texto plano | Uso de `auth.User`, `set_password`, hash Argon2 y migracion que elimina el campo legado de contrasena. | `codigo_qr/settings.py`, `app/views.py`, `app/migrations/0009_secure_user_profiles_and_weightreading.py` | Cumple |
| RIE-002: ausencia de politica de contrasenas | Largo minimo 12, complejidad, validadores Django, caducidad de 120 dias y bloqueo temporal por intentos fallidos. | `app/password_validators.py`, `app/forms.py`, `app/views.py`, `codigo_qr/settings.py` | Cumple para piloto |
| RIE-003: falta de respaldo y continuidad | Backup consistente SQLite, integridad, SHA-256, restauracion controlada, poda y comando de mantenimiento programable. | `app/services/backup_service.py`, `app/management/commands/*.py`, `docs/security/OPERATIONS_SECURITY.md` | Cumple tecnicamente para piloto; programar ejecución diaria en el PC de sede |
| RIE-004: sin autenticacion institucional | Login local fortalecido, dominios INACAP obligatorios, bloqueo de intentos y autorización de sede para el piloto. | `app/forms.py`, `app/views.py`, `docs/security/PILOT_AUTHORIZATIONS.md` | Control compensatorio aceptado para piloto; SSO sigue requerido para produccion |
| RIE-005: uso de logo institucional | Marca configurable y autorización de sede registrada para el piloto. | `codigo_qr/settings.py`, `docs/security/PILOT_AUTHORIZATIONS.md` | Cumple para piloto autorizado |
| RIE-006: ausencia de SAST | Script reproducible con Bandit y salida externa en `..\Archivos personales Proyecto Balanza\Resultados\security`. | `requirements-dev.txt`, `scripts/security_check.ps1`, `scripts/security_check.sh` | Cumple como capacidad reproducible; ejecutar y conservar reportes |
| RIE-007: ausencia de DAST | Wrapper OWASP ZAP baseline via Docker. | `scripts/dast_zap.ps1`, `scripts/dast_zap.sh` | Cumple como capacidad reproducible; ejecutar con servidor levantado |
| RIE-008: librerias obsoletas o vulnerables | `pip check`, `pip-audit` sobre `requirements.txt` y dependencia dev versionada. | `requirements.txt`, `requirements-dev.txt`, `scripts/security_check.*` | Cumple como proceso verificable |
| RIE-009: falta de estandares de desarrollo seguro | Checklist, seguridad web Django, auditoria, roles, retencion, incidentes y flujo SDLC documentado. | `PREDEPLOY_CHECKLIST.md`, `README.md`, `docs/security/*.md` | Cumple para piloto; produccion debe pasar por metodologia GST |

## Evidencia minima para una entrega

Ejecutar antes de entregar o desplegar:

```powershell
.\scripts\setup.ps1 -SkipInstall
.\scripts\security_check.ps1 -InstallTools
python manage.py backup_sqlite
python manage.py purge_old_data
```

Para DAST, levantar el servidor local y ejecutar:

```powershell
python manage.py runserver
.\scripts\dast_zap.ps1 -TargetUrl http://host.docker.internal:8000
```

Los reportes generados quedan fuera del código, en `..\Archivos personales Proyecto Balanza\Resultados\security\`.
