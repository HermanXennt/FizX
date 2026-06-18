from django.contrib import admin

from .models import Meeting, MeetingParticipant


class MeetingParticipantInline(admin.TabularInline):
    model = MeetingParticipant
    extra = 0
    autocomplete_fields = ["user"]
    readonly_fields = ("joined_at", "left_at", "created_at")


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "room_name", "host", "status", "scheduled_start", "created_at")
    list_filter = ("status", "waiting_room_enabled")
    search_fields = ("title", "room_name", "host__phone_number")
    readonly_fields = ("id", "room_name", "password_hash", "actual_start", "actual_end", "created_at", "updated_at")
    autocomplete_fields = ["host", "workspace", "parent_meeting"]
    inlines = [MeetingParticipantInline]


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ("user", "meeting", "role", "status", "joined_at", "left_at")
    list_filter = ("role", "status")
    search_fields = ("user__phone_number", "meeting__title")
    autocomplete_fields = ["user", "meeting"]
