from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalogue.models import Country, Program


class SiteSitemap(Sitemap):
    changefreq = "weekly"
    protocol = "http" if settings.DEBUG else "https"


class StaticPages(SiteSitemap):
    priority = 0.8

    def items(self):
        return ["web:home", "web:country_list", "web:program_list", "web:book"]

    def location(self, item):
        return reverse(item)


class Countries(SiteSitemap):
    priority = 0.9

    def items(self):
        return Country.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class Programs(SiteSitemap):
    priority = 0.7

    def items(self):
        return Program.objects.visible()

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {"pages": StaticPages, "countries": Countries, "programs": Programs}
