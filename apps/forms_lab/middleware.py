class SimpleHtmxDetails:
    def __init__(self, request):
        self.request = request

    def __bool__(self):
        return self.request.headers.get("HX-Request") == "true"


class SimpleHtmxMiddleware:
    """Tiny request.htmx compatibility shim when django-htmx is not installed."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.htmx = SimpleHtmxDetails(request)
        return self.get_response(request)
