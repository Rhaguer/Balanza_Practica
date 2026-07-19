from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    """Enforces the project's password complexity policy."""

    def __init__(self, min_length=8, max_length=12):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, password, user=None):
        password = password or ""
        errors = []

        if len(password) < self.min_length:
            errors.append(
                ValidationError(
                    _("La contraseña debe tener al menos %(min_length)d caracteres."),
                    code="password_too_short",
                    params={"min_length": self.min_length},
                )
            )

        if len(password) > self.max_length:
            errors.append(
                ValidationError(
                    _("La contraseña no puede superar %(max_length)d caracteres."),
                    code="password_too_long",
                    params={"max_length": self.max_length},
                )
            )

        if not any(char.islower() for char in password):
            errors.append(
                ValidationError(
                    _("La contraseña debe incluir al menos una letra minúscula."),
                    code="password_no_lowercase",
                )
            )

        if not any(char.isupper() for char in password):
            errors.append(
                ValidationError(
                    _("La contraseña debe incluir al menos una letra mayúscula."),
                    code="password_no_uppercase",
                )
            )

        if not any(char.isdigit() for char in password):
            errors.append(
                ValidationError(
                    _("La contraseña debe incluir al menos un número."),
                    code="password_no_digit",
                )
            )

        if not any(not char.isalnum() and not char.isspace() for char in password):
            errors.append(
                ValidationError(
                    _("La contraseña debe incluir al menos un carácter especial."),
                    code="password_no_special",
                )
            )

        if any(char.isspace() for char in password):
            errors.append(
                ValidationError(
                    _("La contraseña no debe contener espacios."),
                    code="password_whitespace",
                )
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Debe tener entre %(min_length)d y %(max_length)d caracteres e incluir "
            "mayúsculas, minúsculas, números y un carácter especial, sin espacios."
        ) % {
            "min_length": self.min_length,
            "max_length": self.max_length,
        }
