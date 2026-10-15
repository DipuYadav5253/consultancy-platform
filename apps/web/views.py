from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.catalogue.models import Country, Program, University

from .forms import ProgramFilterForm, filter_programs

DEFAULT_DESTINATIONS = [
    "United Kingdom",
    "Canada",
    "Australia",
    "United States",
    "Ireland",
    "Germany",
]


def visible_programs():
    """Only programs whose university and country are published as well."""
    return Program.objects.visible().select_related("university__country")


@require_GET
def home(request):
    countries = list(Country.objects.filter(is_published=True))
    # The strip needs enough names to look full, so a nearly empty catalogue uses the defaults.
    names = [c.name for c in countries] if len(countries) >= 4 else DEFAULT_DESTINATIONS
    return render(
        request,
        "home.html",
        {
            "countries": countries,
            "destination_names": names,
            "featured_programs": visible_programs().order_by("-updated_at")[:6],
            "levels": Program.Level.choices,
        },
    )


@require_GET
def country_list(request):
    countries = Country.objects.filter(is_published=True).annotate(
        program_count=Count(
            "universities__programs",
            filter=Q(universities__is_published=True, universities__programs__is_published=True),
            distinct=True,
        )
    )
    return render(request, "web/country_list.html", {"countries": countries})


@require_GET
def country_detail(request, slug):
    country = get_object_or_404(Country, slug=slug, is_published=True)
    universities = (
        University.objects.visible()
        .filter(country=country)
        .annotate(
            program_count=Count("programs", filter=Q(programs__is_published=True), distinct=True)
        )
    )
    programs = visible_programs().filter(university__country=country).order_by("name")
    return render(
        request,
        "web/country_detail.html",
        {
            "country": country,
            "universities": universities,
            "programs": programs[:6],
            "program_total": programs.count(),
        },
    )


@require_GET
def program_list(request):
    form = ProgramFilterForm(request.GET)
    queryset = visible_programs()
    if form.is_valid():
        queryset = filter_programs(queryset, form.cleaned_data)
    else:
        queryset = queryset.order_by("name")
    page = Paginator(queryset, 12).get_page(request.GET.get("page"))
    filtered = any(request.GET.get(name) for name in form.fields)
    return render(
        request,
        "web/program_list.html",
        {"form": form, "page": page, "filtered": filtered},
    )


@require_GET
def program_detail(request, slug):
    program = get_object_or_404(visible_programs(), slug=slug)
    related = visible_programs().filter(university=program.university).exclude(pk=program.pk)[:3]
    return render(request, "web/program_detail.html", {"program": program, "related": related})


@require_GET
def book(request):
    return render(request, "web/book.html")


@require_GET
def robots(request):
    # The admin path is deliberately NOT listed: robots.txt is public and would reveal it.
    sitemap = request.build_absolute_uri(reverse("sitemap"))
    body = f"User-agent: *\nAllow: /\nDisallow: /account/\n\nSitemap: {sitemap}\n"
    return HttpResponse(body, content_type="text/plain")
