from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def enviar_confirmacion_registro_usuario(usuario, login_url):
    nombre = (usuario.nombre or "").strip()
    apellido = (usuario.apellido or "").strip()
    nombre_completo = f"{nombre} {apellido}".strip() or usuario.email
    rol = usuario.grupo_principal

    asunto = "Confirmación de registro"
    texto = (
        f"Hola {nombre_completo},\n\n"
        "Tu usuario ya está registrado en el Sistema de Gestión de Residuos.\n"
        f"Correo de acceso: {usuario.email}\n"
        f"Rol asignado: {rol}\n"
        f"Ingreso al sistema: {login_url}\n\n"
        "Por seguridad, la contraseña no se incluye en este correo.\n"
        "Si no reconoces este registro, comunícate con el administrador del sistema."
    )
    html = f"""
        <div style="font-family:Arial,sans-serif;color:#1f2937;line-height:1.6">
          <h2 style="color:#0f766e">Usuario registrado correctamente</h2>
          <p>Hola {escape(nombre_completo)},</p>
          <p>Tu usuario ya está registrado en el Sistema de Gestión de Residuos.</p>
          <table style="border-collapse:collapse;margin:18px 0">
            <tr>
              <td style="padding:8px 12px;font-weight:bold;background:#f3f4f6">Correo</td>
              <td style="padding:8px 12px;border:1px solid #e5e7eb">{escape(usuario.email)}</td>
            </tr>
            <tr>
              <td style="padding:8px 12px;font-weight:bold;background:#f3f4f6">Rol</td>
              <td style="padding:8px 12px;border:1px solid #e5e7eb">{escape(rol)}</td>
            </tr>
          </table>
          <p>
            <a href="{escape(login_url)}"
               style="display:inline-block;padding:10px 18px;background:#0f766e;color:white;text-decoration:none;border-radius:6px">
              Ingresar al sistema
            </a>
          </p>
          <p><strong>Por seguridad, la contraseña no se incluye en este correo.</strong></p>
          <p style="color:#6b7280;font-size:13px">
            Si no reconoces este registro, comunícate con el administrador del sistema.
          </p>
        </div>
    """

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[usuario.email],
    )
    mensaje.attach_alternative(html, "text/html")
    return mensaje.send(fail_silently=False)
