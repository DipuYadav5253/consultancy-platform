from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
]

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
