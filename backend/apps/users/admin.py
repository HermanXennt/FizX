from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ("phone_number", "full_name", "is_staff", "is_active", "presence_status", "created_at")
    list_filter = ("is_staff", "is_active", "presence_status")
    search_fields = ("phone_number", "first_name", "last_name")
    readonly_fields = ("id", "created_at", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("phone_number",)}),
        ("Profile", {"fields": ("first_name", "last_name", "avatar", "timezone")}),
        ("Status", {"fields": ("presence_status", "last_seen_at")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    filter_horizontal = ("groups", "user_permissions")
