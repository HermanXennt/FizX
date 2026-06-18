import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from apps.core.models import BaseModel


def generate_room_name() -> str:
    return f"room-{uuid.uuid4().hex[:16]}"


class MeetingStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    LIVE = "live", "Live"
    ENDED = "ended", "Ended"
    CANCELLED = "cancelled", "Cancelled"


class Meeting(BaseModel):
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="meetings", null=True, blank=True
    )
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_meetings")
    title = models.CharField(max_length=200, default="Untitled Meeting")
    description = models.TextField(blank=True)
    room_name = models.CharField(max_length=64, unique=True, default=generate_room_name)

    status = models.CharField(max_length=20, choices=MeetingStatus.choices, default=MeetingStatus.SCHEDULED)

    password_hash = models.CharField(max_length=200, blank=True)
    waiting_room_enabled = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(default=100)

    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    recurrence_rule = models.CharField(max_length=200, blank=True)
    parent_meeting = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="occurrences"
    )
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "meetings"
        ordering = ["-scheduled_start", "-created_at"]
        indexes = [models.Index(fields=["room_name"]), models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"{self.title} ({self.room_name})"

    @property
    def requires_password(self) -> bool:
        return bool(self.password_hash)

    @property
    def is_recurring_template(self) -> bool:
        return bool(self.recurrence_rule) and self.parent_meeting_id is None

    def set_password(self, raw_password: str | None) -> None:
        self.password_hash = make_password(raw_password) if raw_password else ""

    def check_password(self, raw_password: str | None) -> bool:
        if not self.requires_password:
            return True
        if not raw_password:
            return False
        return check_password(raw_password, self.password_hash)


class ParticipantRole(models.TextChoices):
    HOST = "host", "Host"
    CO_HOST = "co_host", "Co-Host"
    PARTICIPANT = "participant", "Participant"


class ParticipantStatus(models.TextChoices):
    INVITED = "invited", "Invited"
    WAITING = "waiting", "Waiting"
    ADMITTED = "admitted", "Admitted"
    LEFT = "left", "Left"
    DENIED = "denied", "Denied"
    REMOVED = "removed", "Removed"


class MeetingParticipant(BaseModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meeting_participations")
    role = models.CharField(max_length=20, choices=ParticipantRole.choices, default=ParticipantRole.PARTICIPANT)
    status = models.CharField(max_length=20, choices=ParticipantStatus.choices, default=ParticipantStatus.INVITED)

    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)

    is_muted = models.BooleanField(default=False)
    hand_raised = models.BooleanField(default=False)

    class Meta:
        db_table = "meeting_participants"
        constraints = [
            models.UniqueConstraint(fields=["meeting", "user"], name="unique_meeting_participant"),
        ]
        ordering = ["-role", "created_at"]

    def __str__(self) -> str:
        return f"{self.user.phone_number} in {self.meeting.room_name} ({self.status})"

    @property
    def livekit_identity(self) -> str:
        return str(self.user_id)
