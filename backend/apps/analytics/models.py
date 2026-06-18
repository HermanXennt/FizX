from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class AnalyticsEventType(models.TextChoices):
    FEATURE_USED = "feature_used", "Feature Used"
    PAGE_VIEWED = "page_viewed", "Page Viewed"
    ERROR_ENCOUNTERED = "error_encountered", "Error Encountered"
    GENERIC = "generic", "Generic"


class AnalyticsEvent(BaseModel):
    """Freeform client-side usage events (feature adoption, page views, etc).

    Meeting/attendance/recording statistics are *not* duplicated here - those are
    derived directly from the Meeting, MeetingParticipant, and MeetingRecording
    tables in services.py, which are the authoritative source of truth and can
    never drift out of sync with a separately-logged event stream.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_events"
    )
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_events"
    )
    event_type = models.CharField(max_length=30, choices=AnalyticsEventType.choices, default=AnalyticsEventType.GENERIC)
    name = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "analytics_events"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["event_type", "name", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.event_type}:{self.name}"
