from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .services import NotificationService


@database_sync_to_async
def _set_presence_on_connect(user):
    from apps.users.models import PresenceStatus

    if user.presence_status == PresenceStatus.OFFLINE:
        from apps.users.services import UserService

        UserService().update_presence(user=user, presence_status=PresenceStatus.ONLINE)


@database_sync_to_async
def _set_presence_on_disconnect(user):
    from apps.users.models import PresenceStatus

    user.refresh_from_db()
    if user.presence_status == PresenceStatus.ONLINE:
        from apps.users.services import UserService

        UserService().update_presence(user=user, presence_status=PresenceStatus.OFFLINE)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Personal notification + presence channel. One group per user (`notifications_<user_id>`),
    joined by every browser tab/device that user has open."""

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f"notifications_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await _set_presence_on_connect(user)

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await _set_presence_on_disconnect(self.user)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")
        try:
            if msg_type == "mark_read":
                await database_sync_to_async(NotificationService().mark_read)(
                    notification_id=content.get("notification_id"), user=self.user
                )
            elif msg_type == "mark_all_read":
                await database_sync_to_async(NotificationService().mark_all_read)(user=self.user)
        except Exception:  # noqa: BLE001 - never let a bad client payload kill the socket
            await self.send_json({"type": "error", "detail": "Could not process that request."})

    async def notification_message(self, event):
        await self.send_json({"type": "notification.created", "notification": event["notification"]})
