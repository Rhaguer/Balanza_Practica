(function () {
    "use strict";

    var button = document.querySelector("[data-copy-target]");
    var status = document.querySelector("[data-copy-status]");
    if (!button || !status) return;

    function announce(message) {
        status.textContent = message;
    }

    async function copyText(text) {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return;
        }

        var input = document.createElement("textarea");
        input.value = text;
        input.setAttribute("readonly", "");
        input.className = "visually-hidden";
        document.body.appendChild(input);
        input.select();
        var copied = document.execCommand("copy");
        input.remove();
        if (!copied) throw new Error("copy-not-supported");
    }

    button.addEventListener("click", async function () {
        var target = document.getElementById(button.dataset.copyTarget);
        var text = target?.textContent?.trim() || "";
        if (!text) {
            announce("No existe un enlace disponible para copiar.");
            return;
        }

        try {
            await copyText(text);
            announce("Enlace copiado correctamente.");
        } catch (error) {
            announce("No fue posible copiar automáticamente. Selecciona el enlace y cópialo manualmente.");
        }
    });
})();
