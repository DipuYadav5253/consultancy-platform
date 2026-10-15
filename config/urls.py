from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from two_factor.urls import urlpatterns as two_factor_urls

from apps.web.sitemaps import sitemaps

urlpatterns = [
    path("", include("apps.core.urls")),
    path("", include("apps.web.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("", include(two_factor_urls)),
    path(settings.ADMIN_URL, admin.site.urls),
]

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
