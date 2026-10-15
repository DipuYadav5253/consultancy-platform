from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

from apps.core.models import PublishableModel, TimeStampedModel

currency_validator = RegexValidator(r"^[A-Z]{3}$", "Use a 3-letter currency code, e.g. GBP.")
iso_validator = RegexValidator(r"^[A-Z]{2}$", "Use a 2-letter country code, e.g. GB.")


class Country(TimeStampedModel, PublishableModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    iso_code = models.CharField(max_length=2, unique=True, validators=[iso_validator])
    currency = models.CharField(max_length=3, validators=[currency_validator])
    summary = models.TextField(blank=True)
    intakes = models.CharField(max_length=200, blank=True, help_text="e.g. September, January")
    living_cost_per_year_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    living_cost_per_year_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    visa_overview = models.TextField(blank=True)
    scholarships_overview = models.TextField(blank=True)
    last_reviewed_on = models.DateField(
        null=True, blank=True, help_text="Rules change: date someone last checked this page."
    )
    source_url = models.URLField(blank=True, help_text="Official source for the visa facts.")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "countries"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("web:country_detail", args=[self.slug])

    def clean(self):
        super().clean()
        if self.is_published and not self.last_reviewed_on:
            raise ValidationError("A published country needs a 'last reviewed on' date.")
        low, high = self.living_cost_per_year_min, self.living_cost_per_year_max
        if low is not None and high is not None and low > high:
            raise ValidationError("Minimum living cost cannot be higher than the maximum.")


class UniversityQuerySet(models.QuerySet):
    def visible(self):
        """Publicly visible: the university and its country are both published."""
        return self.filter(is_published=True, country__is_published=True)


class University(TimeStampedModel, PublishableModel):
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="universities")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    city = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    ranking_note = models.CharField(max_length=200, blank=True)

    objects = UniversityQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "universities"
        constraints = [
            models.UniqueConstraint(fields=["country", "name"], name="uniq_university_per_country"),
        ]

    def __str__(self):
        return self.name


class ProgramQuerySet(models.QuerySet):
    def visible(self):
        """Publicly visible: the program, its university and the country are all published."""
        return self.filter(
            is_published=True,
            university__is_published=True,
            university__country__is_published=True,
        )


class Program(TimeStampedModel, PublishableModel):
    class Level(models.TextChoices):
        FOUNDATION = "foundation", "Foundation"
        DIPLOMA = "diploma", "Diploma"
        BACHELOR = "bachelor", "Bachelor's"
        MASTER = "master", "Master's"
        PHD = "phd", "PhD"

    university = models.ForeignKey(University, on_delete=models.PROTECT, related_name="programs")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    level = models.CharField(max_length=20, choices=Level.choices, db_index=True)
    field_of_study = models.CharField(max_length=100, db_index=True)
    duration_months = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    tuition_per_year = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        db_index=True,
    )
    tuition_currency = models.CharField(max_length=3, validators=[currency_validator])
    intakes = models.CharField(max_length=200, blank=True)
    ielts_min = models.DecimalField(
        "IELTS overall minimum",
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(9)],
        db_index=True,
    )
    pte_min = models.PositiveSmallIntegerField(
        "PTE Academic minimum",
        null=True,
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(90)],
    )
    description = models.TextField(blank=True)

    objects = ProgramQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["university", "name", "level"], name="uniq_program_per_university_level"
            ),
            models.CheckConstraint(
                condition=Q(ielts_min__isnull=True) | Q(ielts_min__gte=0, ielts_min__lte=9),
                name="program_ielts_between_0_and_9",
            ),
            models.CheckConstraint(
                condition=Q(pte_min__isnull=True) | Q(pte_min__gte=10, pte_min__lte=90),
                name="program_pte_between_10_and_90",
            ),
            models.CheckConstraint(
                condition=Q(duration_months__gte=1), name="program_duration_positive"
            ),
            models.CheckConstraint(
                condition=Q(tuition_per_year__isnull=True) | Q(tuition_per_year__gte=0),
                name="program_tuition_not_negative",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_level_display()}), {self.university}"

    def get_absolute_url(self):
        return reverse("web:program_detail", args=[self.slug])
