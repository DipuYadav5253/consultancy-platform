from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from two_factor.urls import urlpatterns as two_factor_urls

urlpatterns = [
    path("", include("apps.core.urls")),
    path("", include(two_factor_urls)),
    path(settings.ADMIN_URL, admin.site.urls),
]

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
