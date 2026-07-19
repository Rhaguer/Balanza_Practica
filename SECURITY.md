# Seguridad del proyecto

Documentacion principal:

- `docs/security/COMPLIANCE_MATRIX.md`: trazabilidad contra el informe RIE-001 a RIE-009.
- `docs/security/OPERATIONS_SECURITY.md`: instalacion, backup, restauracion, retencion, continuidad e incidentes.
- `docs/security/TESTING_AND_AUDIT.md`: SAST, DAST y auditoria de dependencias.
- `docs/security/SSO_AND_BRAND.md`: autenticacion institucional y uso de marca.
- `docs/security/SECURE_SDLC.md`: estandar minimo de desarrollo seguro.

## Reporte de incidentes durante piloto

Registrar:

- Fecha y hora.
- Usuario o equipo afectado.
- Accion observada.
- Evidencia en `logs/django.log` y `AuditLog`.
- Backup disponible mas reciente.
- Medida aplicada.

Antes de investigar, preservar copia de `db.sqlite3`, `logs/` y `backups/`.
