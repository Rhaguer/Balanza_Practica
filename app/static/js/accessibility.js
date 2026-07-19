(function () {
    "use strict";

    var api = window.SiteAccessibility;
    if (!api) return;

    var state = api.read();
    var systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
    var coarsePointer = window.matchMedia("(pointer: coarse)");
    var widgets = Array.from(document.querySelectorAll("[data-a11y-widget]"));

    function persist() {
        try {
            window.localStorage.setItem(api.storageKey, JSON.stringify(state));
        } catch (error) {
            // El componente sigue operativo en memoria si el almacenamiento está bloqueado.
        }
    }

    function resolvedTheme() {
        if (state.theme !== "system") return state.theme;
        return systemTheme.matches ? "dark" : "light";
    }

    function applyState() {
        state = api.apply(state);
        document.documentElement.dataset.a11yTheme = resolvedTheme();
        widgets.forEach(syncWidget);
    }

    function announce(widget, message) {
        var status = widget.querySelector("[data-a11y-status]");
        if (!status) return;
        status.textContent = "";
        window.setTimeout(function () {
            status.textContent = message;
        }, 20);
    }

    function syncWidget(widget) {
        var scale = widget.querySelector("[data-a11y-text-scale]");
        var value = widget.querySelector("[data-a11y-text-value]");
        var theme = widget.querySelector("[data-a11y-theme]");
        if (scale) scale.value = String(state.textScale);
        if (value) value.textContent = state.textScale + " %";
        if (theme) theme.value = state.theme;

        widget.querySelectorAll("[data-a11y-toggle]").forEach(function (control) {
            var key = control.dataset.a11yToggle;
            control.checked = Boolean(state[key]);
        });
    }

    function update(widget, message) {
        applyState();
        persist();
        announce(widget, message);
    }

    function firstPanelControl(panel) {
        return panel.querySelector(
            "button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex='-1'])"
        );
    }

    function openPanel(widget) {
        var launcher = widget.querySelector("[data-a11y-open]");
        var panel = widget.querySelector("[data-a11y-panel]");
        var backdrop = widget.querySelector("[data-a11y-backdrop]");
        if (!launcher || !panel || !backdrop) return;

        panel.hidden = false;
        backdrop.hidden = false;
        launcher.setAttribute("aria-expanded", "true");
        launcher.setAttribute("aria-label", "Cerrar menú de accesibilidad");
        window.requestAnimationFrame(function () {
            panel.classList.add("is-open");
            firstPanelControl(panel)?.focus();
        });
    }

    function closePanel(widget, restoreFocus) {
        var launcher = widget.querySelector("[data-a11y-open]");
        var panel = widget.querySelector("[data-a11y-panel]");
        var backdrop = widget.querySelector("[data-a11y-backdrop]");
        if (!launcher || !panel || panel.hidden) return;

        panel.classList.remove("is-open");
        panel.hidden = true;
        if (backdrop) backdrop.hidden = true;
        launcher.setAttribute("aria-expanded", "false");
        launcher.setAttribute("aria-label", "Abrir menú de accesibilidad");
        if (restoreFocus) launcher.focus();
    }

    function reset(widget) {
        state = api.defaults();
        try {
            window.localStorage.removeItem(api.storageKey);
        } catch (error) {
            // El estado en memoria igualmente vuelve a sus valores predeterminados.
        }
        applyState();
        announce(widget, "Opciones de accesibilidad restablecidas.");
    }

    widgets.forEach(function (widget) {
        var launcher = widget.querySelector("[data-a11y-open]");
        var panel = widget.querySelector("[data-a11y-panel]");
        var backdrop = widget.querySelector("[data-a11y-backdrop]");
        var scale = widget.querySelector("[data-a11y-text-scale]");
        var theme = widget.querySelector("[data-a11y-theme]");
        if (!launcher || !panel) return;

        syncWidget(widget);
        launcher.addEventListener("click", function () {
            if (panel.hidden) openPanel(widget);
            else closePanel(widget, true);
        });
        widget.querySelector("[data-a11y-close]")?.addEventListener("click", function () {
            closePanel(widget, true);
        });
        backdrop?.addEventListener("click", function () {
            closePanel(widget, true);
        });
        scale?.addEventListener("input", function () {
            state.textScale = Number(scale.value);
            update(widget, "Tamaño del texto: " + state.textScale + " por ciento.");
        });
        theme?.addEventListener("change", function () {
            state.theme = theme.value;
            update(widget, "Apariencia actualizada.");
        });
        widget.querySelectorAll("[data-a11y-toggle]").forEach(function (control) {
            control.addEventListener("change", function () {
                var key = control.dataset.a11yToggle;
                state[key] = control.checked;
                update(widget, control.closest("label")?.querySelector("strong")?.textContent + (
                    control.checked ? " activado." : " desactivado."
                ));
            });
        });
        widget.querySelector("[data-a11y-reset]")?.addEventListener("click", function () {
            reset(widget);
        });
    });

    document.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;
        widgets.forEach(function (widget) {
            var panel = widget.querySelector("[data-a11y-panel]");
            if (panel && !panel.hidden) closePanel(widget, true);
        });
    });

    document.addEventListener("pointermove", function (event) {
        if (!state.readingGuide || coarsePointer.matches) return;
        document.documentElement.style.setProperty("--a11y-guide-y", event.clientY + "px");
    }, { passive: true });

    systemTheme.addEventListener?.("change", function () {
        if (state.theme === "system") applyState();
    });
    coarsePointer.addEventListener?.("change", applyState);

    applyState();
})();
