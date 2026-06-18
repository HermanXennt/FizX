from django.contrib import admin

from .models import MeetingRecording


@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    list_display = ("egress_id", "meeting", "status", "duration_seconds", "started_at", "ended_at")
    list_filter = ("status",)
    search_fields = ("egress_id", "meeting__title")
    autocomplete_fields = ["meeting", "requested_by"]
    readonly_fields = ("id", "egress_id", "created_at", "updated_at")
