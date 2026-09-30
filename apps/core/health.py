import logging

from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def liveness():
    """The process is running. Load balancers use this to decide whether to restart it."""
    return JsonResponse({"status": "ok"})


def readiness():
    """The database answers. Load balancers only send traffic to servers that are ready."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        logger.exception("Readiness check failed")
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})
