# Pruebas SAST, DAST y auditoria de dependencias

Este documento define como generar evidencia tecnica para cubrir los riesgos RIE-006, RIE-007 y RIE-008.

## Preparacion

Crear entorno y dependencias:

```powershell
.\scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

En Linux/macOS:

```bash
bash scripts/setup.sh
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Revision automatizada completa

Windows:

```powershell
.\scripts\security_check.ps1 -InstallTools -DastTargetUrl http://127.0.0.1:8000
```

Linux/macOS:

```bash
DAST_TARGET_URL=http://127.0.0.1:8000 bash scripts/security_check.sh --install-tools
```

El script ejecuta:

- `python manage.py check`
- `python manage.py check --deploy`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test`
- `python -m pip check`
- `bandit -r app codigo_qr -x app/migrations`
- `pip-audit -r requirements.txt`

Los reportes quedan fuera del código, en
`..\Archivos personales Proyecto Balanza\Resultados\security\`.

Si el `.env` local usa `DJANGO_DEBUG=True`, `check --deploy` puede mostrar advertencias esperadas. Para validar la configuracion productiva sin modificar `.env`, ejecutar:

```powershell
.\scripts\deploy_check.ps1
```

Linux/macOS:

```bash
bash scripts/deploy_check.sh
```

## SAST manual

```powershell
python -m bandit -r app codigo_qr -x app/migrations -f txt -o "../Archivos personales Proyecto Balanza/Resultados/security/bandit.txt"
```

Criterio de aceptacion:

- Revisar hallazgos High y Medium.
- Corregir hallazgos explotables.
- Justificar falsos positivos en el reporte de entrega.

## Auditoria de dependencias

```powershell
python -m pip_audit -r requirements.txt -f json -o "../Archivos personales Proyecto Balanza/Resultados/security/pip_audit.json"
```

Criterio de aceptacion:

- No debe existir vulnerabilidad critica sin plan de mitigacion.
- Si una dependencia no tiene version corregida compatible, registrar excepcion temporal.

## DAST con OWASP ZAP

Antes de ZAP se puede ejecutar la prueba dinámica local incluida, sin Docker:

```powershell
python scripts\dast_smoke.py http://127.0.0.1:8000
```

Esta prueba comprueba cabeceras, protección de rutas, token de balanza y rechazo CSRF. No reemplaza
el análisis completo de OWASP ZAP, pero entrega evidencia repetible para el piloto local.

1. Levantar el servidor:

```powershell
python manage.py runserver 0.0.0.0:8000
```

2. Ejecutar baseline con Docker:

```powershell
.\scripts\dast_zap.ps1 -TargetUrl http://host.docker.internal:8000
```

Linux/macOS:

```bash
bash scripts/dast_zap.sh http://host.docker.internal:8000
```

El reporte HTML queda en `..\Archivos personales Proyecto Balanza\Resultados\security\zap_baseline.html`.

Criterio de aceptacion:

- Revisar alertas High y Medium.
- Corregir hallazgos aplicables.
- Registrar falsos positivos o limitaciones del piloto.

## Checklist de evidencia

Antes de entregar:

- Adjuntar `..\Archivos personales Proyecto Balanza\Resultados\security\security_check_*.txt`.
- Adjuntar `..\Archivos personales Proyecto Balanza\Resultados\security\bandit_*.txt`.
- Adjuntar `..\Archivos personales Proyecto Balanza\Resultados\security\pip_audit_*.json`.
- Adjuntar `..\Archivos personales Proyecto Balanza\Resultados\security\zap_baseline.html` si se ejecuto DAST.
- Registrar version de commit o fecha de carpeta entregada.
