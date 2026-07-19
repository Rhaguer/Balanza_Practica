(function () {
    "use strict";

    var STORAGE_KEY = "site.a11y.v1";
    var ROOT = document.documentElement;
    var TEXT_SCALES = [100, 125, 150, 175, 200];
    var THEMES = ["system", "light", "dark"];
    var BOOLEAN_KEYS = [
        "contrast",
        "grayscale",
        "readableFont",
        "highlightLinks",
        "reduceMotion",
    ];

    function defaults() {
        return {
            textScale: 100,
            theme: "system",
            contrast: false,
            grayscale: false,
            readableFont: false,
            highlightLinks: false,
            readingGuide: false,
            reduceMotion: false,
        };
    }

    function validate(candidate) {
        var safe = defaults();
        if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
            return safe;
        }

        if (TEXT_SCALES.indexOf(Number(candidate.textScale)) !== -1) {
            safe.textScale = Number(candidate.textScale);
        }
        if (THEMES.indexOf(candidate.theme) !== -1) {
            safe.theme = candidate.theme;
        }
        BOOLEAN_KEYS.forEach(function (key) {
            if (typeof candidate[key] === "boolean") {
                safe[key] = candidate[key];
            }
        });
        return safe;
    }

    function read() {
        try {
            return validate(JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null"));
        } catch (error) {
            return defaults();
        }
    }

    function apply(state) {
        var safe = validate(state);
        TEXT_SCALES.forEach(function (scale) {
            ROOT.classList.toggle("a11y-text-" + scale, safe.textScale === scale);
        });
        THEMES.forEach(function (theme) {
            if (theme !== "system") {
                ROOT.classList.toggle("a11y-theme-" + theme, safe.theme === theme);
            }
        });
        BOOLEAN_KEYS.forEach(function (key) {
            var className = "a11y-" + key.replace(/[A-Z]/g, function (letter) {
                return "-" + letter.toLowerCase();
            });
            ROOT.classList.toggle(className, safe[key]);
        });
        ROOT.dataset.a11yReady = "true";
        return safe;
    }

    window.SiteAccessibility = {
        storageKey: STORAGE_KEY,
        defaults: defaults,
        validate: validate,
        read: read,
        apply: apply,
        allowedTextScales: TEXT_SCALES.slice(),
        allowedThemes: THEMES.slice(),
        booleanKeys: BOOLEAN_KEYS.slice(),
    };

    apply(read());
})();
