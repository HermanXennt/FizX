from django.contrib import admin

from .models import Invitation, Workspace, WorkspaceMember


class WorkspaceMemberInline(admin.TabularInline):
    model = WorkspaceMember
    extra = 0
    autocomplete_fields = ["user"]
    readonly_fields = ("created_at",)


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "plan", "created_at")
    list_filter = ("plan",)
    search_fields = ("name", "slug")
    readonly_fields = ("id", "slug", "created_at", "updated_at")
    inlines = [WorkspaceMemberInline]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "workspace", "role", "status", "expires_at", "created_at")
    list_filter = ("status", "role")
    search_fields = ("phone_number", "workspace__name")
    readonly_fields = ("id", "token", "created_at", "updated_at")
    autocomplete_fields = ["workspace", "invited_by"]
