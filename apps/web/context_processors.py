from django.conf import settings

from apps.catalogue.models import Country


def site(request):
    """Values every page needs: brand name, contact email and destinations for the footer."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "footer_countries": Country.objects.filter(is_published=True).only("name", "slug")[:6],
    }
