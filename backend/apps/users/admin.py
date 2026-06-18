from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "full_name", "is_verified", "is_staff", "is_active", "presence_status", "created_at")
    list_filter = ("is_staff", "is_active", "is_verified", "auth_provider", "presence_status")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("id", "created_at", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "avatar", "timezone")}),
        ("Status", {"fields": ("auth_provider", "is_verified", "presence_status", "last_seen_at")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    filter_horizontal = ("groups", "user_permissions")
