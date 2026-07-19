(function () {
    const DEFAULT_DURATION = 10000;
    const queue = [];
    let active = false;

    function normalizeType(type) {
        const value = String(type || "info").toLowerCase();
        if (value.includes("danger") || value.includes("error")) return "error";
        if (value.includes("warn")) return "warning";
        if (value.includes("success")) return "success";
        if (value.includes("confirm")) return "confirm";
        return "info";
    }

    function defaultsFor(type) {
        return {
            success: { title: "Operación realizada", icon: "✓" },
            error: { title: "No se pudo completar", icon: "!" },
            warning: { title: "Atención", icon: "!" },
            confirm: { title: "Confirmar acción", icon: "?" },
            info: { title: "Información", icon: "i" },
        }[type];
    }

    function showNext() {
        if (active || queue.length === 0) return;
        active = true;
        const item = queue.shift();
        const type = normalizeType(item.options.type);
        const defaults = defaultsFor(type);
        const duration = Number(item.options.duration) || DEFAULT_DURATION;
        const isConfirm = Boolean(item.options.confirm);

        const overlay = document.createElement("div");
        overlay.className = "app-popup-overlay";
        overlay.setAttribute("role", "presentation");
        overlay.innerHTML = `
            <section class="app-popup-dialog" role="dialog" aria-modal="true">
                <header class="app-popup-header">
                    <span class="app-popup-icon" aria-hidden="true"></span>
                    <h2 class="app-popup-title"></h2>
                </header>
                <div class="app-popup-body"></div>
                <div class="app-popup-actions">
                    <button type="button" class="app-popup-button app-popup-button-secondary" data-popup-cancel>Cancelar</button>
                    <button type="button" class="app-popup-button app-popup-button-primary" data-popup-accept>Aceptar</button>
                </div>
                <div class="app-popup-progress" aria-hidden="true">
                    <div class="app-popup-progress-bar"></div>
                </div>
            </section>
        `;

        const dialog = overlay.querySelector(".app-popup-dialog");
        const accept = overlay.querySelector("[data-popup-accept]");
        const cancel = overlay.querySelector("[data-popup-cancel]");
        dialog.dataset.type = isConfirm ? "confirm" : type;
        overlay.querySelector(".app-popup-icon").textContent = defaults.icon;
        overlay.querySelector(".app-popup-title").textContent =
            item.options.title || defaults.title;
        overlay.querySelector(".app-popup-body").textContent =
            String(item.options.message || "");
        accept.textContent = item.options.acceptText || (isConfirm ? "Confirmar" : "Aceptar");
        cancel.textContent = item.options.cancelText || "Cancelar";
        cancel.hidden = !isConfirm;
        if (isConfirm && item.options.danger !== false) {
            accept.classList.remove("app-popup-button-primary");
            accept.classList.add("app-popup-button-danger");
        }
        overlay.querySelector(".app-popup-progress-bar").style.animationDuration = `${duration}ms`;

        let finished = false;
        let timer = null;
        function escapeHandler(event) {
            if (event.key !== "Escape" || finished) return;
            close(isConfirm ? false : true);
        }

        function close(result) {
            if (finished) return;
            finished = true;
            window.clearTimeout(timer);
            document.removeEventListener("keydown", escapeHandler);
            overlay.remove();
            active = false;
            item.resolve(result);
            window.setTimeout(showNext, 0);
        }

        accept.addEventListener("click", function () { close(true); });
        cancel.addEventListener("click", function () { close(false); });
        overlay.addEventListener("click", function (event) {
            if (event.target === overlay) close(isConfirm ? false : true);
        });
        document.addEventListener("keydown", escapeHandler);

        document.body.appendChild(overlay);
        accept.focus();
        timer = window.setTimeout(function () {
            close(isConfirm ? false : true);
        }, duration);
    }

    function enqueue(options) {
        return new Promise(function (resolve) {
            queue.push({ options: options || {}, resolve });
            showNext();
        });
    }

    window.AppPopup = {
        alert: function (message, options) {
            return enqueue({ ...(options || {}), message, confirm: false });
        },
        confirm: function (message, options) {
            return enqueue({
                type: "confirm",
                ...(options || {}),
                message,
                confirm: true,
            });
        },
    };

    window.alert = function (message) {
        return window.AppPopup.alert(message, { type: "info" });
    };

    document.addEventListener("submit", async function (event) {
        const form = event.target;
        const message = form?.dataset?.confirmMessage;
        if (!message || form.dataset.confirmed === "true") return;

        event.preventDefault();
        const submitter = event.submitter;
        const confirmed = await window.AppPopup.confirm(message, {
            title: form.dataset.confirmTitle || "Confirmar acción",
            acceptText: form.dataset.confirmAccept || "Confirmar",
            danger: form.dataset.confirmDanger !== "false",
        });
        if (!confirmed) return;

        form.dataset.confirmed = "true";
        if (typeof form.requestSubmit === "function") {
            form.requestSubmit(submitter || undefined);
            window.setTimeout(function () {
                delete form.dataset.confirmed;
            }, 0);
        } else {
            form.submit();
        }
    }, true);

    document.addEventListener("DOMContentLoaded", function () {
        const messages = document.querySelectorAll(
            ".alert.alert-success, .alert.alert-danger, .alert.alert-warning, .alert.alert-info"
        );
        messages.forEach(function (element) {
            if (element.hidden || element.classList.contains("hidden")) return;
            const message = (element.textContent || "").trim();
            if (!message) return;
            const type = Array.from(element.classList).find(function (name) {
                return name.startsWith("alert-") && name !== "alert-dismissible";
            }) || "alert-info";
            element.remove();
            window.AppPopup.alert(message, { type });
        });
    });
})();
