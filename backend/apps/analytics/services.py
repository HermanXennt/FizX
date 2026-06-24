from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.meetings.models import Meeting, MeetingParticipant, MeetingStatus, ParticipantStatus
from apps.recordings.models import MeetingRecording, RecordingStatus

from .models import AnalyticsEvent
from .repositories import AnalyticsEventRepository

MEETING_DURATION = ExpressionWrapper(F("actual_end") - F("actual_start"), output_field=DurationField())
PARTICIPANT_DURATION = ExpressionWrapper(F("left_at") - F("joined_at"), output_field=DurationField())


def _minutes(duration: timedelta | None) -> float:
    if not duration:
        return 0.0
    return round(duration.total_seconds() / 60, 1)


class WorkspaceAnalyticsService:
    def get_overview(self, *, workspace, since_days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=since_days)
        meetings = Meeting.objects.filter(workspace=workspace, actual_start__isnull=False)

        total_meetings = meetings.count()
        total_duration = meetings.filter(actual_end__isnull=False).annotate(
            duration=MEETING_DURATION
        ).aggregate(total=Sum("duration"))["total"]

        ended_meetings = meetings.filter(status=MeetingStatus.ENDED, actual_end__isnull=False)
        avg_duration = ended_meetings.annotate(duration=MEETING_DURATION).aggregate(avg=Avg("duration"))["avg"]
        avg_minutes = _minutes(avg_duration)

        meetings_by_day = list(
            meetings.filter(actual_start__gte=since)
            .annotate(day=TruncDate("actual_start"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        top_hosts = list(
            meetings.values("host__id", "host__first_name", "host__last_name", "host__phone_number")
            .annotate(meeting_count=Count("id"))
            .order_by("-meeting_count")[:5]
        )

        total_recordings = MeetingRecording.objects.filter(
            meeting__workspace=workspace, status=RecordingStatus.READY
        ).count()

        return {
            "total_meetings": total_meetings,
            "total_meeting_minutes": _minutes(total_duration),
            "avg_meeting_duration_minutes": avg_minutes,
            "total_recordings": total_recordings,
            "meetings_by_day": [{"date": row["day"], "count": row["count"]} for row in meetings_by_day],
            "top_hosts": [
                {
                    "user_id": row["host__id"],
                    "name": f"{row['host__first_name']} {row['host__last_name']}".strip()
                    or row["host__phone_number"],
                    "meeting_count": row["meeting_count"],
                }
                for row in top_hosts
            ],
        }

    def get_student_roster(self, *, workspace, since_days: int = 30) -> list[dict]:
        """Per-student attendance summary for a teacher's workspace - the
        "needs attention" signal (zero/low attendance) a teacher actually
        needs, which the meeting-count/duration-only workspace overview above
        doesn't break down per person."""
        from apps.workspaces.models import WorkspaceMember, WorkspaceRole

        since = timezone.now() - timedelta(days=since_days)
        total_meetings = Meeting.objects.filter(workspace=workspace, actual_start__gte=since).count()
        members = WorkspaceMember.objects.filter(workspace=workspace, role=WorkspaceRole.MEMBER).select_related("user")

        roster = []
        for member in members:
            participations = MeetingParticipant.objects.filter(
                user=member.user, meeting__workspace=workspace, joined_at__gte=since, joined_at__isnull=False
            )
            attended_count = participations.values("meeting_id").distinct().count()
            duration = participations.annotate(duration=PARTICIPANT_DURATION).aggregate(total=Sum("duration"))["total"]
            last_attended = participations.order_by("-joined_at").values_list("joined_at", flat=True).first()

            roster.append(
                {
                    "user_id": member.user.id,
                    "name": member.user.full_name,
                    "meetings_attended": attended_count,
                    "total_meetings": total_meetings,
                    "total_minutes": _minutes(duration),
                    "last_attended": last_attended,
                }
            )

        return sorted(roster, key=lambda r: r["meetings_attended"])


class UserAnalyticsService:
    def get_my_stats(self, *, user, since_days: int = 56) -> dict:
        since = timezone.now() - timedelta(days=since_days)

        hosted = Meeting.objects.filter(host=user, actual_start__isnull=False)
        hosted_count = hosted.count()

        attended = MeetingParticipant.objects.filter(
            user=user, status=ParticipantStatus.LEFT, joined_at__isnull=False, left_at__isnull=False
        )
        attended_duration = attended.annotate(duration=PARTICIPANT_DURATION).aggregate(total=Sum("duration"))[
            "total"
        ]

        attended_count = MeetingParticipant.objects.filter(
            user=user, joined_at__isnull=False
        ).count()

        weekly = list(
            MeetingParticipant.objects.filter(user=user, joined_at__gte=since, joined_at__isnull=False)
            .annotate(day=TruncDate("joined_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return {
            "meetings_hosted": hosted_count,
            "meetings_attended": attended_count,
            "total_minutes_in_meetings": _minutes(attended_duration),
            "activity_by_day": [{"date": row["day"], "count": row["count"]} for row in weekly],
        }


class AnalyticsEventService:
    def __init__(self, repository: AnalyticsEventRepository | None = None):
        self.repository = repository or AnalyticsEventRepository()

    def log(self, *, user=None, workspace=None, event_type: str, name: str, metadata: dict | None = None) -> AnalyticsEvent:
        return AnalyticsEvent.objects.create(
            user=user, workspace=workspace, event_type=event_type, name=name, metadata=metadata or {}
        )
