from django.shortcuts import render
from django.views.decorators.http import require_GET

from . import health


@require_GET
def home(request):
    return render(request, "home.html")


@require_GET
def healthz(request):
    return health.liveness()


@require_GET
def readyz(request):
    return health.readiness()


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)
