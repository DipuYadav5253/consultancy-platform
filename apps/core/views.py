from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from . import health


@require_GET
def healthz(request):
    return health.liveness()


@require_GET
def readyz(request):
    return health.readiness()


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    # Rendered without a request on purpose: if the database is the problem, the normal
    # page context would fail again and hide the real error.
    return HttpResponseServerError(render_to_string("errors/500.html"))
