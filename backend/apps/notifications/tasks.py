import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger("apps.notifications")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_email_task(self, notification_id: str):
    from .models import Notification

    try:
        notification = Notification.objects.select_related("recipient").get(id=notification_id)
    except Notification.DoesNotExist:
        logger.warning("send_notification_email_task: notification %s no longer exists", notification_id)
        return

    context = {
        "title": notification.title,
        "body": notification.body,
        "action_url": notification.data.get("action_url"),
    }

    try:
        text_body = render_to_string("emails/notification.txt", context)
        html_body = render_to_string("emails/notification.html", context)
        message = EmailMultiAlternatives(
            subject=notification.title,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.recipient.email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send notification email to %s", notification.recipient.email)
        raise self.retry(exc=exc) from exc
