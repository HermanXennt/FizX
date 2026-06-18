from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class RecordingStatus(models.TextChoices):
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class MeetingRecording(BaseModel):
    meeting = models.ForeignKey("meetings.Meeting", on_delete=models.CASCADE, related_name="recordings")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="started_recordings"
    )
    egress_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=RecordingStatus.choices, default=RecordingStatus.PROCESSING)
    file_url = models.CharField(max_length=500, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    size_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "meeting_recordings"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["egress_id"])]

    def __str__(self) -> str:
        return f"Recording {self.egress_id} ({self.status})"
