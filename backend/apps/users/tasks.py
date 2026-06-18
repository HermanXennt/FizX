import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger("apps.users")


def _send_html_email(subject: str, to_email: str, template_base: str, context: dict) -> None:
    text_body = render_to_string(f"emails/{template_base}.txt", context)
    html_body = render_to_string(f"emails/{template_base}.html", context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_verification_email_task(self, user_id: str, verification_url: str):
    from .models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning("send_verification_email_task: user %s no longer exists", user_id)
        return

    try:
        _send_html_email(
            subject="Verify your FizX email address",
            to_email=user.email,
            template_base="verify_email",
            context={"first_name": user.first_name, "verification_url": verification_url},
        )
    except Exception as exc:  # noqa: BLE001 - retry on any transient SMTP failure
        logger.exception("Failed to send verification email to %s", user.email)
        raise self.retry(exc=exc) from exc


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email_task(self, user_id: str, reset_url: str):
    from .models import User

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning("send_password_reset_email_task: user %s no longer exists", user_id)
        return

    try:
        _send_html_email(
            subject="Reset your FizX password",
            to_email=user.email,
            template_base="password_reset",
            context={"first_name": user.first_name, "reset_url": reset_url},
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send password reset email to %s", user.email)
        raise self.retry(exc=exc) from exc
