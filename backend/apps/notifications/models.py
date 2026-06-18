from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class NotificationType(models.TextChoices):
    MEETING_INVITE = "meeting_invite", "Meeting Invite"
    MEETING_REMINDER = "meeting_reminder", "Meeting Reminder"
    MEETING_STARTING = "meeting_starting", "Meeting Starting"
    WORKSPACE_INVITE = "workspace_invite", "Workspace Invite"
    RECORDING_READY = "recording_ready", "Recording Ready"
    MENTIONED_IN_CHAT = "mentioned_in_chat", "Mentioned in Chat"
    ROLE_CHANGED = "role_changed", "Role Changed"
    GENERIC = "generic", "Generic"


class Notification(BaseModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.GENERIC)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.type} -> {self.recipient_id}"
