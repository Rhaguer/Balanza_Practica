class MinimalPermissionsPolicyMiddleware:
    """Bloquea APIs sensibles que esta aplicación no necesita."""

    POLICY = (
        "camera=(), microphone=(), geolocation=(), payment=(), "
        "usb=(), browsing-topics=()"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Permissions-Policy", self.POLICY)
        return response
