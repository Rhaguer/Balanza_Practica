(function () {
    function activarControlesDeContrasena() {
        document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
            if (button.dataset.passwordToggleReady === 'true') return;

            const input = document.getElementById(button.dataset.passwordToggle);
            if (!input) return;

            button.dataset.passwordToggleReady = 'true';
            button.addEventListener('click', function () {
                const mostrar = input.type === 'password';
                const etiqueta = mostrar ? 'Ocultar contraseña' : 'Mostrar contraseña';

                input.type = mostrar ? 'text' : 'password';
                button.setAttribute('aria-pressed', String(mostrar));
                button.setAttribute('aria-label', etiqueta);
                button.setAttribute('title', etiqueta);

                try {
                    input.focus({ preventScroll: true });
                    const final = input.value.length;
                    input.setSelectionRange(final, final);
                } catch (error) {
                    input.focus();
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', activarControlesDeContrasena);
    } else {
        activarControlesDeContrasena();
    }
})();
