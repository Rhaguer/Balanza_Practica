# Accesibilidad global, seguridad y verificación

Fecha de revisión: 2026-07-18

## Alcance y declaración

Este documento registra la implementación y las pruebas del componente global de
accesibilidad, el encabezado, el título de QR y el footer institucional.

El resultado no es una certificación legal, WCAG ni OWASP. Una certificación exige
auditoría independiente, revisión jurídica, validación de infraestructura y pruebas
humanas con tecnologías de asistencia.

## Resultado implementado

- Botón real `Accesibilidad` en el extremo derecho del header, con objetivo mínimo
  de 44 x 44 px y disponible en las plantillas de la aplicación, login y
  administración de Django.
- Panel operable mediante mouse y teclado con texto 100, 125, 150, 175 y 200 %;
  apariencia del sistema, clara y oscura; alto contraste; escala de grises; fuente
  de lectura; enlaces resaltados; guía de lectura; movimiento reducido y
  restablecimiento.
- Preferencias no personales en `localStorage`, clave `site.a11y.v1`, valores
  validados por listas permitidas y funcionamiento en memoria cuando el
  almacenamiento está bloqueado.
- Enlace de salto como primer elemento enfocable, `lang="es-CL"`, landmarks
  `header`, `nav`, `main`, `aside` y `footer`, foco visible y anuncios `aria-live`.
- Logo INACAP intrínseco 604 x 114 px y renderizado a 150 x 28 px en escritorio.
- Footer fijo de 61 px, de lado a lado, sin separación del borde inferior y con
  fondo `#475569`, igual al header.
- Ocho enlaces sociales reales. Cada icono se presenta en tarjeta blanca cuadrada
  de 28 x 28 px en escritorio y 23 x 23 px en móvil, con pictograma negro. En
  `hover` y `focus-visible` cambia al color de marca; Instagram usa su gradiente.
- Título `QR para registrar residuos` dentro de una franja roja con texto blanco.
- Cabecera HTTP `Permissions-Policy` mínima para APIs que la aplicación no usa:
  cámara, micrófono, geolocalización, pagos, USB y browsing topics.

## Archivos de esta implementación

| Archivo | Función |
| --- | --- |
| `app/templates/includes/accessibility_widget.html` | Componente reutilizable y estados ARIA. |
| `app/templates/base.html` | Header, componente, main, footer, logo y enlaces sociales globales. |
| `app/templates/login.html` | Estructura semántica y componente en la ruta pública. |
| `templates/admin/base_site.html` | Integra el mismo componente en administración. |
| `app/templates/codigo_qr.html` | Título y estructura accesible de QR. |
| `app/static/js/accessibility-init.js` | Validación y aplicación temprana de preferencias. |
| `app/static/js/accessibility.js` | Interacción, teclado, persistencia, guía y reset. |
| `app/static/css/accessibility.css` | Panel, focos, temas, contraste, reflow y movimiento. |
| `app/static/css/accessibility-admin.css` | Posición del componente en Django admin. |
| `app/static/css/base.css` | Medidas del header/footer y estados de redes sociales. |
| `app/static/css/profesor.css` | Compatibilidad del header y navegación responsive. |
| `app/static/css/login.css` | Contraste del ingreso. |
| `app/static/css/institutional_theme.css` | Contraste de utilidades y dashboard. |
| `app/static/css/codigo_qr.css` | Presentación del título, tarjeta y QR. |
| `app/static/fotos/logo-footer.png` | Logo institucional 604 x 114 px. |
| `app/middleware.py` | `Permissions-Policy` restrictiva. |
| `codigo_qr/settings.py` | Middleware y resolución de plantillas administrativas. |
| `app/test_accessibility.py` | Regresión de estructura, seguridad del JS y admin. |
| `app/tests.py` | Regresión de los ocho enlaces del footer. |
| `scripts/axe_audit.mjs` | Auditoría axe-core de rutas representativas. |
| `scripts/accessibility_ui_test.mjs` | Prueba funcional, teclado, persistencia y hover. |
| `scripts/dast_smoke.py` | DAST no destructivo de cabeceras y controles de acceso. |
| `package.json`, `package-lock.json` | Versiones reproducibles de axe y Selenium. |
| `.gitignore` | Excluye `node_modules`. |

## Matriz WCAG 2.2 AA

| Criterio o grupo | Estado | Evidencia o pendiente |
| --- | --- | --- |
| 1.1.1 Contenido no textual | Cumplido en el alcance | Logo y QR tienen `alt`; SVG decorativos usan `aria-hidden`. Revisar manualmente futuras imágenes. |
| 1.2 Multimedia | No aplicable hoy | No se encontraron elementos `video`, `audio` ni pistas multimedia. |
| 1.3.1 Información y relaciones | Cumplido en rutas auditadas | Landmarks, fieldset, legend, label, tablas y estructura de plantillas. |
| 1.3.2 Secuencia significativa | Cumplido en componente | Orden DOM y de foco lógico; sin reordenamiento visual que altere lectura. |
| 1.4.1 Uso del color | Cumplido en componente | Estados incluyen texto, icono, borde o forma además de color. |
| 1.4.3 y 1.4.11 Contraste | Cumplido en rutas axe | Cero problemas `critical/serious`; incluye claro, oscuro y foco. Revisión humana final recomendada. |
| 1.4.4 Cambio de tamaño | Cumplido en componente | Texto seleccionable hasta 200 %, unidades relativas y valor visible. |
| 1.4.10 Reflow | Cumplido técnicamente | 320, 375, 768, 1024 y 1440 CSS px sin scroll horizontal con texto al 200 %. |
| 1.4.12 Espaciado de texto | Pendiente humano | No se ejecutó una matriz manual completa con espaciado personalizado. |
| 1.4.13 Contenido en hover/foco | Cumplido | El footer no oculta contenido y replica hover mediante `focus-visible`. |
| 2.1.1 y 2.1.2 Teclado y sin trampa | Cumplido | Enter, Espacio, Tab, Shift+Tab y Escape probados; el foco vuelve al lanzador. |
| 2.2.2 Pausar movimiento | Cumplido | Opción explícita y respeto de `prefers-reduced-motion`. |
| 2.4.1 Evitar bloques | Cumplido en aplicación | Enlace de salto visible al foco y destino `main-content`. |
| 2.4.3 y 2.4.7 Foco | Cumplido | Orden lógico y foco de 3 px de alto contraste. |
| 2.4.6 Encabezados y etiquetas | Cumplido en componente | Nombres descriptivos. La jerarquía completa de futuras vistas requiere control continuo. |
| 2.5.3 Etiqueta en el nombre | Cumplido | El nombre accesible contiene el texto visible. |
| 2.5.8 Tamaño del objetivo | Cumplido en componente | Lanzador y controles principales tienen al menos 44 px. |
| 3.2.1 y 3.2.2 Predecible | Cumplido | Ningún control cambia de contexto solo por foco; cambios son solicitados. |
| 3.3 Formularios y errores | Parcial / preexistente | Django asocia campos y errores principales; falta auditoría manual exhaustiva de todos los formularios. |
| 4.1.2 Nombre, función y valor | Cumplido | `button`, `aria-expanded`, `aria-controls`, labels y estados nativos. |
| 4.1.3 Mensajes de estado | Cumplido | Región `role="status"` y `aria-live="polite"`. |
| Gráficos de canvas | Pendiente humano | El dashboard muestra valores textuales cercanos, pero debe validarse que toda tendencia tenga alternativa equivalente. |
| NVDA con Chrome/Firefox | Pendiente humano | NVDA no está disponible en este entorno automatizado. |
| Zoom real de navegador 400 % | Pendiente humano | Se validó el equivalente de reflow a 320 CSS px y texto al 200 %; falta prueba manual del control de zoom del navegador. |
| Validador HTML W3C | Pendiente | No se envió contenido autenticado a un servicio externo. Axe y pruebas DOM sí se ejecutaron. |

## Matriz OWASP ASVS 5.0, orientación nivel 2

Esta matriz no equivale a una verificación ASVS L2 completa.

| Área | Estado | Evidencia o pendiente |
| --- | --- | --- |
| Codificación y sanitización | Cumplido para el componente | Plantilla autoescapada, `textContent`, clases conocidas; sin `innerHTML`, `eval`, `Function` ni `document.write`. |
| Validación de entrada | Cumplido en componente / parcial global | Preferencias mediante allowlist; formularios y APIs conservan validación de servidor. Revisión exhaustiva de cada regla de negocio queda pendiente. |
| Autenticación | Cumplido para piloto | Django auth, Argon2, política de contraseña, bloqueo temporal y mensajes genéricos. SSO institucional sigue pendiente para producción. |
| Sesiones | Cumplido por configuración | HttpOnly, SameSite Lax, edad configurable, rotación de sesión de Django y Secure en producción. |
| Control de acceso | Cumplido en pruebas representativas | Rutas protegidas redirigen; API de balanza exige token; permisos se validan en vistas. Una revisión IDOR manual completa sigue pendiente. |
| CSRF | Cumplido | Middleware activo, formularios POST con token y POST anónimo sin CSRF rechazado. |
| Acceso a datos | Cumplido por arquitectura | ORM Django y consultas parametrizadas; Bandit sin hallazgos. |
| Criptografía y secretos | Cumplido en configuración | Argon2 y secretos desde entorno; producción rechaza la clave de desarrollo. Gestión institucional de secretos requiere infraestructura. |
| Transporte seguro | Condicionado a infraestructura | Redirect, cookies Secure y HSTS configurables. HSTS solo debe activarse tras comprobar HTTPS en dominio y subdominios. |
| Cabeceras | Parcial | `nosniff`, `DENY`, Referrer-Policy, COOP de Django y Permissions-Policy comprobadas. CSP aplicable queda pendiente. |
| CSP y frontend | Pendiente preexistente | Bootstrap, Tailwind y Chart.js remotos, más scripts/estilos inline existentes, impiden una CSP estricta sin refactor previo. No se debilitó CSP. |
| Privacidad | Cumplido para el componente | Solo preferencias visuales no personales, sin red, analítica, logs ni perfiles. |
| Archivos | No aplicable al componente | El componente no carga archivos. Descargas y respaldos conservan autorización existente. |
| Registro y errores | Parcial | Logs rotativos y errores productivos de Django; revisar minimización de datos personales en una auditoría operacional. |
| Dependencias | Cumplido al 2026-07-18 | `pip-audit` y `npm audit`: cero vulnerabilidades conocidas en los manifiestos auditados. |
| SAST y DAST | Cumplido en alcance local | Bandit sin hallazgos y DAST smoke sin fallas. ZAP Baseline completo pendiente porque Docker no está instalado. |

Referencias técnicas: [WCAG](https://www.w3.org/WAI/standards-guidelines/wcag/),
[OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/),
[OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/) y
[OWASP Top 10](https://owasp.org/www-project-top-ten/).

## Aplicabilidad legal chilena

| Norma | Evaluación |
| --- | --- |
| Ley 20.422 | Línea base pertinente para igualdad de oportunidades, accesibilidad y diseño universal. La implementación aporta controles técnicos, pero la aplicabilidad jurídica concreta y el cumplimiento integral requieren revisión legal. |
| Ley 19.628 | Aplicable al tratamiento existente de usuarios y correos. El componente no agrega datos personales. Deben mantenerse finalidad, seguridad, acceso, rectificación, cancelación y retención. |
| Ley 21.719 | A la fecha del informe aún no entra en vigencia; comienza el 1 de diciembre de 2026. El diseño minimiza datos y evita inferir discapacidad, pero la preparación organizacional exige revisión jurídica y operacional. |
| Decreto 1/2015 MINSEGPRES | Aplicación directa solo si el sistema pertenece a un órgano de la Administración del Estado. No hay evidencia suficiente en el repositorio para afirmarlo; se usa como referencia técnica. |
| Ley 21.663 | No se puede afirmar que INACAP o este piloto sea servicio esencial u operador de importancia vital solo desde el código. Requiere determinación jurídica/ANCI. Se usa como referencia de gestión de incidentes. |
| Ley 21.459 | Contexto penal de prevención de acceso ilícito, alteración, fraude y abuso de dispositivos; no certifica controles técnicos. |

Fuentes oficiales: [Ley 20.422](https://www.bcn.cl/leychile/navegar?idNorma=1010903),
[Decreto 1/2015](https://www.bcn.cl/leychile/navegar?idNorma=1078308),
[Ley 19.628](https://www.bcn.cl/leychile/Navegar?idNorma=141599&idParte=8642680),
[Ley 21.719](https://www.bcn.cl/leychile/navegar?idNorma=1209272),
[Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434) y
[Ley 21.459](https://www.bcn.cl/leychile/navegar?idNorma=1177743).

## Pruebas ejecutadas

| Comando o prueba | Resultado real |
| --- | --- |
| `python manage.py test app` | 84/84 OK en la versión final. |
| `python manage.py test app.test_accessibility` | 8/8 OK. |
| `python manage.py check` | Sin problemas. |
| `python manage.py makemigrations --check --dry-run` | Sin cambios de modelos. |
| `python manage.py check --deploy` mediante `deploy_check.ps1` | Sin advertencias con perfil seguro aislado. |
| `npm run test:a11y` | Cero problemas axe `critical/serious` en login, administración, dashboard, talleres y QR. |
| `npm run test:a11y-ui` | Teclado, apertura/cierre, combinación, recarga, navegación, persistencia, reset y hover: OK. |
| Matriz visual | 320, 375, 768, 1024 y 1440 px, texto 200 %, sin desplazamiento horizontal. |
| `bandit -r app codigo_qr ...` | Sin hallazgos. |
| `pip-audit -r requirements.txt` | Sin vulnerabilidades conocidas. |
| `npm audit` | Cero vulnerabilidades. |
| `scripts/dast_smoke.py` | Cabeceras, rutas protegidas, token y CSRF: OK. |
| `git diff --check` | Sin errores de espacios; solo advertencias preexistentes de conversión LF/CRLF. |
| OWASP ZAP Baseline | No ejecutado: `docker` no está instalado en este equipo. |

El reporte reproducible de seguridad se generó en:

`..\Archivos personales Proyecto Balanza\Resultados\security\security_check_20260718_222532.txt`

## Problemas preexistentes y riesgos residuales

- El repositorio ya estaba ampliamente modificado antes de esta tarea. No se
  revirtieron ni normalizaron cambios ajenos.
- La CSP estricta está pendiente por dependencias CDN y código inline preexistente.
- Los gráficos `canvas` requieren confirmación humana de equivalencia textual.
- Falta prueba manual con NVDA y zoom real al 400 %.
- Falta ejecutar ZAP Baseline cuando Docker esté disponible.
- La revisión jurídica de aplicabilidad y la auditoría ASVS L2 independiente no
  pueden resolverse solo mediante código.
- Los enlaces sociales dependen de sitios externos; no cargan contenido remoto
  hasta que el usuario los activa.

## Configuración de producción

1. Completar `.env.production.example` con secretos reales fuera del repositorio.
2. Mantener `DJANGO_DEBUG=False`, hosts y orígenes HTTPS explícitos.
3. Confirmar el proxy y `X-Forwarded-Proto` antes de activar redirect SSL.
4. Activar HSTS solamente después de comprobar HTTPS en todo el dominio. No usar
   `INCLUDE_SUBDOMAINS` ni preload sin verificar todos los subdominios.
5. Migrar Bootstrap, Tailwind y Chart.js a archivos locales, retirar estilos y
   scripts inline, y luego desplegar una CSP por etapas: primero Report-Only,
   revisar reportes y finalmente enforcement.
6. Ejecutar `collectstatic`, `deploy_check.ps1`, suite completa, auditoría de
   dependencias y DAST en un entorno no productivo.

## Reversión

1. Respaldar la base de datos y el árbol actual.
2. Revertir únicamente los archivos de la tabla “Archivos de esta implementación”;
   no usar `git reset --hard` en este worktree porque contiene cambios del usuario.
3. Retirar `MinimalPermissionsPolicyMiddleware` de `MIDDLEWARE` si se revierte
   `app/middleware.py`.
4. Retirar `BASE_DIR / "templates"` de `TEMPLATES[0]["DIRS"]` si se elimina el
   override administrativo.
5. Ejecutar `collectstatic --noinput`, `manage.py check` y la suite completa.
6. Borrar únicamente `site.a11y.v1` en el navegador si se desea eliminar las
   preferencias guardadas; no limpiar todo `localStorage`.

## Repetición local

```powershell
venv\Scripts\python.exe manage.py collectstatic --noinput
venv\Scripts\python.exe manage.py test app
venv\Scripts\python.exe manage.py check
venv\Scripts\python.exe manage.py makemigrations --check --dry-run
$env:AXE_TEST_USERNAME="usuario-de-prueba"
$env:AXE_TEST_PASSWORD="clave-de-prueba"
npm ci
npm run test:a11y
npm run test:a11y-ui
powershell -File scripts\security_check.ps1 -DastTargetUrl http://127.0.0.1:8000
```
