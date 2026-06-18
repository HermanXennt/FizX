from django.contrib import admin

from .models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "name", "user", "workspace", "created_at")
    list_filter = ("event_type",)
    search_fields = ("name", "user__phone_number")
    autocomplete_fields = ["user", "workspace"]
    readonly_fields = ("id", "created_at", "updated_at")
