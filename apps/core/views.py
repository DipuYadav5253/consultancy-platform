import logging

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def home(request):
    return render(request, "home.html")


@require_GET
def healthz(request):
    """Liveness: the process is running. The load balancer uses this to restart it."""
    return JsonResponse({"status": "ok"})


@require_GET
def readyz(request):
    """Readiness: the database answers. The load balancer only sends traffic when ready."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Readiness check failed")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
