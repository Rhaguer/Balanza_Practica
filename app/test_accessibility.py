from pathlib import Path

from django.contrib.auth.models import Group, User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from app.roles import ROL_PROFESOR


class AccessibilityTemplateTests(TestCase):
    def setUp(self):
        group, _ = Group.objects.get_or_create(name=ROL_PROFESOR)
        self.user = User.objects.create_user(
            username="accesibilidad@test.cl",
            email="accesibilidad@test.cl",
            # Credencial ficticia de una base de pruebas aislada.
            password="ClaveSegura9!",  # nosec B106
        )
        self.user.groups.add(group)

    def assert_global_accessibility_structure(self, response):
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('<html lang="es-CL">', content)
        self.assertEqual(content.count('class="skip-link"'), 1)
        self.assertIn('href="#main-content"', content)
        self.assertIn('id="main-content"', content)
        self.assertEqual(content.count("data-a11y-widget"), 1)
        self.assertEqual(content.count('id="a11y-launcher"'), 1)
        self.assertEqual(content.count('id="a11y-panel"'), 1)
        self.assertIn('aria-expanded="false"', content)
        self.assertIn('aria-controls="a11y-panel"', content)
        self.assertIn('aria-live="polite"', content)
        self.assertIn("Fuente de lectura accesible", content)
        self.assertIn("Guía de lectura", content)
        self.assertIn("Reducir movimiento", content)
        self.assertIn("Restablecer opciones", content)
        self.assertIn("accessibility-init.js", content)
        self.assertIn("accessibility.js", content)
        self.assertIn("accessibility.css", content)

    def test_login_incluye_componente_global_y_salto_al_main(self):
        response = self.client.get(reverse("login"))

        self.assert_global_accessibility_structure(response)
        self.assertIn("camera=()", response.headers["Permissions-Policy"])
        self.assertIn("microphone=()", response.headers["Permissions-Policy"])
        self.assertIn("geolocation=()", response.headers["Permissions-Policy"])
        content = response.content.decode()
        self.assertLess(content.index("skip-link"), content.index("a11y-launcher"))
        self.assertIn("a11y-widget--standalone", content)

    def test_pagina_autenticada_incluye_componente_en_el_header(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("profesor"))

        self.assert_global_accessibility_structure(response)
        content = response.content.decode()
        header_start = content.index("<header>")
        header_end = content.index("</header>", header_start)
        widget_position = content.index("data-a11y-widget")
        self.assertGreater(widget_position, header_start)
        self.assertLess(widget_position, header_end)
        self.assertIn('aria-label="Navegación principal"', content)

    def test_panel_de_sostenibilidad_conserva_componente_global(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))

        self.assert_global_accessibility_structure(response)
        self.assertContains(response, "Panel de Sostenibilidad")

    def test_ingreso_de_administracion_incluye_el_mismo_componente(self):
        response = self.client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertEqual(content.count("data-a11y-widget"), 1)
        self.assertEqual(content.count('id="a11y-launcher"'), 1)
        self.assertIn("accessibility-init.js", content)
        self.assertIn("accessibility.js", content)
        self.assertIn("accessibility-admin.css", content)


class AccessibilityStaticSafetyTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.init_source = (
            cls.project_root / "app" / "static" / "js" / "accessibility-init.js"
        ).read_text(encoding="utf-8")
        cls.component_source = (
            cls.project_root / "app" / "static" / "js" / "accessibility.js"
        ).read_text(encoding="utf-8")
        cls.css_source = (
            cls.project_root / "app" / "static" / "css" / "accessibility.css"
        ).read_text(encoding="utf-8")

    def test_preferencias_usan_clave_versionada_y_lista_permitida(self):
        self.assertIn('"site.a11y.v1"', self.init_source)
        for scale in ("100", "125", "150", "175", "200"):
            self.assertIn(scale, self.init_source)
        for theme in ('"system"', '"light"', '"dark"'):
            self.assertIn(theme, self.init_source)
        self.assertIn("validate", self.init_source)

    def test_componente_no_usa_ejecucion_o_html_dinamico_inseguro(self):
        source = self.init_source + self.component_source
        forbidden = (
            "innerHTML",
            "outerHTML",
            "document.write",
            "eval(",
            "new Function",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_restablecer_elimina_solo_la_preferencia_de_accesibilidad(self):
        self.assertIn("localStorage.removeItem(api.storageKey)", self.component_source)
        self.assertNotIn("localStorage.clear", self.component_source)

    def test_css_incluye_reflow_foco_movimiento_y_objetivos_tactiles(self):
        self.assertIn("@media (max-width: 640px)", self.css_source)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css_source)
        self.assertIn("min-height: 44px", self.css_source)
        self.assertIn(":focus-visible", self.css_source)
        self.assertIn("pointer-events: none", self.css_source)
