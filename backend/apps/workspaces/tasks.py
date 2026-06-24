import logging

from celery import shared_task

logger = logging.getLogger("apps.workspaces")


@shared_task
def sync_whatsapp_groups():
    """Runs every 5 minutes. For every workspace linked to a WhatsApp group,
    re-checks its membership and invites anyone new - the "always syncing" half
    of the WhatsApp group import feature (the one-time half is the
    "import-whatsapp-group" action on WorkspaceViewSet)."""
    from apps.integrations.whatsapp_otp import service as whatsapp_otp

    from .models import Workspace
    from .services import InvitationService

    workspaces = Workspace.objects.exclude(whatsapp_group_id="").select_related("whatsapp_linked_by")

    synced = 0
    for workspace in workspaces:
        if workspace.whatsapp_linked_by is None:
            continue
        try:
            phone_numbers = whatsapp_otp.list_group_participants(
                teacher_id=str(workspace.whatsapp_linked_by_id), group_id=workspace.whatsapp_group_id
            )
            InvitationService().bulk_invite_from_whatsapp(
                workspace=workspace, phone_numbers=phone_numbers, invited_by=workspace.whatsapp_linked_by
            )
            synced += 1
        except Exception:  # noqa: BLE001 - one teacher's dead session shouldn't block the rest
            logger.exception("sync_whatsapp_groups: failed for workspace %s", workspace.id)

    logger.info("sync_whatsapp_groups: synced %s of %s linked workspaces", synced, workspaces.count())
    return synced
