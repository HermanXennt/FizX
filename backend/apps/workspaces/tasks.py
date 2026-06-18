import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger("apps.workspaces")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_invitation_email_task(self, invitation_id: str):
    from .models import Invitation

    try:
        invitation = Invitation.objects.select_related("workspace", "invited_by").get(id=invitation_id)
    except Invitation.DoesNotExist:
        logger.warning("send_invitation_email_task: invitation %s no longer exists", invitation_id)
        return

    invitation_url = f"{settings.FRONTEND_URL}/invitations/{invitation.token}"
    context = {
        "inviter_name": invitation.invited_by.full_name if invitation.invited_by else "A teammate",
        "workspace_name": invitation.workspace.name,
        "role": invitation.get_role_display(),
        "invitation_url": invitation_url,
    }

    try:
        text_body = render_to_string("emails/workspace_invitation.txt", context)
        html_body = render_to_string("emails/workspace_invitation.html", context)
        message = EmailMultiAlternatives(
            subject=f"You're invited to join {invitation.workspace.name} on FizX",
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send invitation email to %s", invitation.email)
        raise self.retry(exc=exc) from exc
