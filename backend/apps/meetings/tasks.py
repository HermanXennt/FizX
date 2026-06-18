import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("apps.meetings")


@shared_task
def send_meeting_reminders():
    """Runs every few minutes via Celery Beat. Notifies every invited participant of
    meetings starting in the next 10 minutes that haven't been reminded about yet."""
    from apps.notifications.models import NotificationType
    from apps.notifications.services import NotificationService

    from .models import Meeting, MeetingStatus

    now = timezone.now()
    window_end = now + timezone.timedelta(minutes=10)

    upcoming = Meeting.objects.filter(
        status=MeetingStatus.SCHEDULED,
        scheduled_start__gte=now,
        scheduled_start__lte=window_end,
        reminder_sent_at__isnull=True,
    ).prefetch_related("participants__user")

    notified = 0
    for meeting in upcoming:
        for participant in meeting.participants.all():
            NotificationService().create(
                recipient=participant.user,
                type=NotificationType.MEETING_REMINDER,
                title=f"{meeting.title} starts soon",
                body=f"Starts at {meeting.scheduled_start.strftime('%H:%M UTC')}.",
                data={"meeting_id": str(meeting.id)},
            )
            notified += 1
        meeting.reminder_sent_at = now
        meeting.save(update_fields=["reminder_sent_at", "updated_at"])

    logger.info("send_meeting_reminders: %s meetings, %s notifications sent", upcoming.count(), notified)
    return notified
