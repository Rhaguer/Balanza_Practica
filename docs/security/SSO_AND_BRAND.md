# Autenticacion institucional y uso de marca

## Estado actual

El sistema usa autenticacion local de Django con:

- Hash seguro de contrasenas.
- Politica de complejidad.
- Caducidad obligatoria por `PASSWORD_MAX_AGE_DAYS=120`.
- Auditoria de login exitoso, fallido y contrasena vencida.
- Roles `Administrador`, `Profesor` y `Estudiante`.
- Caducidad obligatoria cada 120 días para el piloto.
- Bloqueo temporal después de cinco intentos fallidos.
- Altas restringidas a `inacap.cl` e `inacapmail.cl`.

La sede autorizó el uso de correo institucional con autenticación local para el alcance del piloto.
Esta autorización está registrada en `docs/security/PILOT_AUTHORIZATIONS.md`.

## Control transitorio para correos institucionales

Para limitar altas de usuarios a dominios autorizados:

```text
ENFORCE_INSTITUTIONAL_EMAIL_DOMAIN=True
INSTITUTIONAL_EMAIL_DOMAINS=inacap.cl,inacapmail.cl
```

Esto no reemplaza SSO, pero reduce el riesgo durante el piloto.

## Integracion SSO requerida para produccion

Para cumplir integracion institucional completa se requiere que GST entregue:

- Proveedor de identidad aprobado: OIDC, SAML o LDAP.
- URL de issuer/metadata.
- Client ID y secreto o certificado.
- URI de retorno autorizada.
- Atributos requeridos: correo, nombre, apellido y grupos/roles.
- Procedimiento de baja o desactivacion de usuarios.
- Responsable de soporte del IdP.

Hasta contar con esos datos, el proyecto no debe declarar SSO productivo. Esta dependencia no
impide el piloto local autorizado, pero sí impide declarar cumplimiento de producción.

## Uso de marca institucional

El uso de logo o imagen institucional queda controlado por:

```text
USE_INSTITUTIONAL_BRAND=False
```

Cuando esta variable es `False`, las pantallas reemplazan el logo por texto generico y el login usa un fondo no institucional.

Para activar marca institucional:

1. Obtener autorizacion formal del area responsable.
2. Registrar fecha, aprobador y alcance permitido.
3. Definir si el uso aplica solo al piloto o tambien a produccion.
4. Cambiar `USE_INSTITUTIONAL_BRAND=True`.

La autorización vigente para el piloto de sede se registra en
`docs/security/PILOT_AUTHORIZATIONS.md`.

La plantilla `.env.production.example` deja la marca desactivada por defecto para evitar uso no autorizado.
