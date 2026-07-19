import sys
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def request_status(opener, base_url, path, method="GET", data=None):
    request = Request(
        urljoin(base_url.rstrip("/") + "/", path.lstrip("/")),
        method=method,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        response = opener.open(request, timeout=10)
        return response.status, response.headers
    except HTTPError as error:
        return error.code, error.headers


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    opener = build_opener(NoRedirect())
    failures = []

    login_status, login_headers = request_status(opener, base_url, "/login/")
    checks = [
        ("login público disponible", login_status == 200, login_status),
        (
            "X-Content-Type-Options",
            login_headers.get("X-Content-Type-Options") == "nosniff",
            login_headers.get("X-Content-Type-Options"),
        ),
        (
            "X-Frame-Options",
            login_headers.get("X-Frame-Options") == "DENY",
            login_headers.get("X-Frame-Options"),
        ),
        (
            "Referrer-Policy",
            login_headers.get("Referrer-Policy") == "same-origin",
            login_headers.get("Referrer-Policy"),
        ),
        (
            "Permissions-Policy mínima",
            all(
                directive in (login_headers.get("Permissions-Policy") or "")
                for directive in ("camera=()", "microphone=()", "geolocation=()")
            ),
            login_headers.get("Permissions-Policy"),
        ),
    ]

    protected_paths = ["/dashboard/", "/backup/base-datos/", "/usuarios/"]
    for path in protected_paths:
        status, _ = request_status(opener, base_url, path)
        checks.append((f"acceso anónimo bloqueado {path}", status in {302, 403}, status))

    weight_status, _ = request_status(
        opener,
        base_url,
        "/api/update_weight/",
        method="POST",
        data=b'{"weight_kg": 1}',
    )
    checks.append(("API de balanza exige token", weight_status in {403, 503}, weight_status))

    csrf_status, _ = request_status(
        opener,
        base_url,
        "/logout/",
        method="POST",
        data=b"{}",
    )
    checks.append(("POST sin CSRF rechazado", csrf_status == 403, csrf_status))

    for name, passed, value in checks:
        print(f"[{'OK' if passed else 'FAIL'}] {name}: {value}")
        if not passed:
            failures.append(name)

    if failures:
        print(f"DAST smoke falló: {', '.join(failures)}", file=sys.stderr)
        return 1

    print("DAST smoke completado sin hallazgos en los controles comprobados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
