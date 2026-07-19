# Autorizaciones del piloto en sede

Fecha de registro: 2026-07-10

Para el piloto local de Balanza de Mermas se deja constancia de que el responsable del proyecto
confirmó las siguientes autorizaciones otorgadas por la sede:

- Uso de imágenes y logotipos institucionales en la interfaz del piloto.
- Uso de correos institucionales INACAP para identificar y crear usuarios.
- Operación con autenticación local de Django mientras el sistema permanezca como piloto de sede.

Alcance:

- Estas autorizaciones aplican al piloto local y no equivalen a una aprobación de producción.
- Si el sistema se publica o integra institucionalmente, se deberá registrar aprobador, vigencia,
  alcance de marca y decisión formal de GST sobre SSO/OIDC/SAML.
- La configuración del piloto mantiene `USE_INSTITUTIONAL_BRAND=True` y
  `ENFORCE_INSTITUTIONAL_EMAIL_DOMAIN=True`.
