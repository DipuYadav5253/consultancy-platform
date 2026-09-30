from django.contrib import admin, messages

from apps.audit.admin_mixins import AuditedAdminMixin

from .models import Country, Program, University


@admin.action(description="Publish selected")
def publish(modeladmin, request, queryset):
    count = 0
    for obj in queryset:  # one by one so validation rules and timestamps apply
        obj.is_published = True
        try:
            obj.full_clean()
        except Exception as exc:
            modeladmin.message_user(request, f"{obj}: {exc}", messages.ERROR)
            continue
        obj.save()
        count += 1
    modeladmin.message_user(request, f"{count} published.", messages.SUCCESS)


@admin.action(description="Unpublish selected (move back to draft)")
def unpublish(modeladmin, request, queryset):
    for obj in queryset:
        obj.is_published = False
        obj.save()
    modeladmin.message_user(request, f"{queryset.count()} moved to draft.", messages.SUCCESS)


@admin.register(Country)
class CountryAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "iso_code", "currency", "is_published", "last_reviewed_on")
    list_filter = ("is_published",)
    search_fields = ("name", "iso_code")
    prepopulated_fields = {"slug": ("name",)}
    actions = [publish, unpublish]
    readonly_fields = ("published_at", "created_at", "updated_at")


@admin.register(University)
class UniversityAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "country", "city", "is_published")
    list_filter = ("is_published", "country")
    search_fields = ("name", "city")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("country",)
    actions = [publish, unpublish]
    readonly_fields = ("published_at", "created_at", "updated_at")


@admin.register(Program)
class ProgramAdmin(AuditedAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "level",
        "university",
        "tuition_per_year",
        "tuition_currency",
        "ielts_min",
        "pte_min",
        "is_published",
    )
    list_filter = ("is_published", "level", "university__country")
    search_fields = ("name", "field_of_study", "university__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("university",)
    actions = [publish, unpublish]
    readonly_fields = ("published_at", "created_at", "updated_at")
