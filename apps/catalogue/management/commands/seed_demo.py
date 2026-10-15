from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalogue.models import Country, Program, University

DEMO_NOTE = "Demo content. Replace or delete it in the admin before launch."

COUNTRIES = [
    ("United Kingdom", "united-kingdom", "GB", "GBP", "September, January"),
    ("Canada", "canada", "CA", "CAD", "September, January, May"),
    ("Australia", "australia", "AU", "AUD", "February, July"),
    ("United States", "united-states", "US", "USD", "Fall, Spring"),
    ("Ireland", "ireland", "IE", "EUR", "September"),
    ("Germany", "germany", "DE", "EUR", "April, October"),
]

# (name, level, field, months, tuition, ielts, pte)
PROGRAMS = [
    ("MSc Data Science", "master", "Data Science", 12, "18500", "6.5", 60),
    ("BSc Business Management", "bachelor", "Business", 36, "15200", "6.0", 54),
    ("MSc Computer Science", "master", "Computer Science", 12, "21000", "6.5", 58),
    ("MBA", "master", "Business", 12, "28000", "7.0", 65),
]


class Command(BaseCommand):
    help = "Create (or remove with --clear) clearly labelled demo catalogue data. Development only."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete the demo data.")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo only runs with DEBUG on (development).")
        if options["clear"]:
            Program.objects.filter(slug__startswith="demo-").delete()
            University.objects.filter(slug__startswith="demo-").delete()
            Country.objects.filter(summary__startswith=DEMO_NOTE).delete()
            self.stdout.write("Demo data removed.")
            return

        for name, slug, iso, currency, intakes in COUNTRIES:
            country, _ = Country.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "iso_code": iso,
                    "currency": currency,
                    "intakes": intakes,
                    "summary": f"{DEMO_NOTE}\n\nA short overview of studying in {name} goes here.",
                    "visa_overview": "Demo text: the student visa route and its official source.",
                    "scholarships_overview": "Demo text: list the main scholarships available.",
                    "living_cost_per_year_min": Decimal("9000"),
                    "living_cost_per_year_max": Decimal("14000"),
                    "last_reviewed_on": date.today(),
                    "source_url": "https://example.com/official-source",
                    "is_published": True,
                },
            )
            for city in ("North", "South"):
                uni, _ = University.objects.get_or_create(
                    slug=f"demo-{slug}-{city.lower()}",
                    defaults={
                        "country": country,
                        "name": f"Demo University {city} ({iso})",
                        "city": f"{city} City",
                        "is_published": True,
                    },
                )
                for pname, level, field, months, tuition, ielts, pte in PROGRAMS:
                    Program.objects.get_or_create(
                        slug=f"demo-{slug}-{city.lower()}-{pname.lower().replace(' ', '-')}",
                        defaults={
                            "university": uni,
                            "name": pname,
                            "level": level,
                            "field_of_study": field,
                            "duration_months": months,
                            "tuition_per_year": Decimal(tuition),
                            "tuition_currency": currency,
                            "ielts_min": Decimal(ielts),
                            "pte_min": pte,
                            "intakes": intakes,
                            "description": "Demo program description.",
                            "is_published": True,
                        },
                    )
        self.stdout.write(self.style.SUCCESS("Demo data created."))
