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


@shared_task
def auto_start_scheduled_meetings():
    """Runs every minute via Celery Beat. Flips a scheduled meeting to live right at
    its scheduled_start even if nobody has joined yet, so it actually starts on time."""
    from .models import Meeting, MeetingStatus
    from .services import MeetingService

    due = Meeting.objects.filter(status=MeetingStatus.SCHEDULED, scheduled_start__lte=timezone.now())
    started = 0
    for meeting in due:
        try:
            MeetingService().start_meeting(meeting=meeting, user=meeting.host)
            started += 1
        except Exception:  # noqa: BLE001 - one bad meeting shouldn't block the rest
            logger.exception("auto_start_scheduled_meetings: failed to start meeting %s", meeting.id)

    logger.info("auto_start_scheduled_meetings: started %s meetings", started)
    return started


@shared_task
def auto_end_overdue_meetings():
    """Runs every minute via Celery Beat. Ends a live meeting once its scheduled_end
    has passed. Meetings with no scheduled_end (instant calls, or scheduled ones left
    open-ended) are never touched here - they only end when the host ends them."""
    from .models import Meeting, MeetingStatus
    from .services import MeetingService

    overdue = Meeting.objects.filter(
        status=MeetingStatus.LIVE, scheduled_end__isnull=False, scheduled_end__lte=timezone.now()
    )
    ended = 0
    for meeting in overdue:
        try:
            MeetingService().end_meeting(meeting=meeting, user=meeting.host)
            ended += 1
        except Exception:  # noqa: BLE001 - one bad meeting shouldn't block the rest
            logger.exception("auto_end_overdue_meetings: failed to end meeting %s", meeting.id)

    logger.info("auto_end_overdue_meetings: ended %s meetings", ended)
    return ended
