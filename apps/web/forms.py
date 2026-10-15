from decimal import Decimal

from django import forms
from django.db.models import F, Q

from apps.catalogue.models import Country, Program

SORT_CHOICES = [
    ("", "Name A to Z"),
    ("tuition", "Lowest tuition first"),
    ("ielts", "Lowest IELTS requirement first"),
]


class ProgramFilterForm(forms.Form):
    country = forms.ModelChoiceField(
        queryset=Country.objects.none(),
        required=False,
        to_field_name="slug",
        empty_label="Any country",
    )
    level = forms.ChoiceField(choices=[("", "Any level"), *Program.Level.choices], required=False)
    q = forms.CharField(
        required=False,
        max_length=100,
        strip=True,
        widget=forms.TextInput(attrs={"placeholder": "Program, field or university"}),
    )
    ielts = forms.DecimalField(
        required=False,
        min_value=Decimal("0"),
        max_value=Decimal("9"),
        max_digits=2,
        decimal_places=1,
        widget=forms.NumberInput(
            attrs={"step": "0.5", "min": "0", "max": "9", "placeholder": "e.g. 6.5"}
        ),
    )
    pte = forms.IntegerField(
        required=False,
        min_value=10,
        max_value=90,
        widget=forms.NumberInput(attrs={"min": "10", "max": "90", "placeholder": "e.g. 60"}),
    )
    max_tuition = forms.DecimalField(
        required=False,
        min_value=Decimal("0"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "100", "min": "0", "placeholder": "e.g. 20000"}),
    )
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["country"].queryset = Country.objects.filter(is_published=True)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("max_tuition") is not None and not cleaned.get("country"):
            self.add_error("max_tuition", "Choose a country so we know which currency to use.")
        return cleaned


def filter_programs(queryset, data):
    """Apply validated search filters. Programs without a listed requirement are never
    counted as matching a score filter, so students are not told they qualify by guesswork."""
    country = data.get("country")
    if country:
        queryset = queryset.filter(university__country=country)
    if data.get("level"):
        queryset = queryset.filter(level=data["level"])
    if data.get("q"):
        term = data["q"]
        queryset = queryset.filter(
            Q(name__icontains=term)
            | Q(field_of_study__icontains=term)
            | Q(university__name__icontains=term)
        )

    ielts, pte = data.get("ielts"), data.get("pte")
    if ielts is not None and pte is not None:
        queryset = queryset.filter(Q(ielts_min__lte=ielts) | Q(pte_min__lte=pte))
    elif ielts is not None:
        queryset = queryset.filter(ielts_min__lte=ielts)
    elif pte is not None:
        queryset = queryset.filter(pte_min__lte=pte)

    if data.get("max_tuition") is not None and country:
        queryset = queryset.filter(
            tuition_per_year__lte=data["max_tuition"], tuition_currency=country.currency
        )

    if data.get("sort") == "tuition":
        return queryset.order_by(F("tuition_per_year").asc(nulls_last=True), "name")
    if data.get("sort") == "ielts":
        return queryset.order_by(F("ielts_min").asc(nulls_last=True), "name")
    return queryset.order_by("name")
