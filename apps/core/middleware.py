from . import health


class HealthCheckMiddleware:
    """Answer /healthz and /readyz before any host or HTTPS checks.

    Load balancers call these by internal IP over plain HTTP. Without this, Django would
    reject them (unknown host) or redirect them (HTTP to HTTPS) and the server would be
    marked unhealthy. This must be the first middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ("GET", "HEAD"):
            if request.path == "/healthz":
                return health.liveness()
            if request.path == "/readyz":
                return health.readiness()
        return self.get_response(request)
