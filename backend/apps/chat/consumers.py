from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.core.utils import to_json_safe

from .repositories import ChannelRepository, MessageRepository
from .serializers import MessageSerializer
from .services import ChatAccessService, MessageService


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope["url_route"]["kwargs"]["channel_id"]
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        channel = await database_sync_to_async(ChannelRepository().get_by_id)(self.channel_id)
        if channel is None:
            await self.close(code=4004)
            return

        has_access = await database_sync_to_async(ChatAccessService().user_has_access)(channel=channel, user=user)
        if not has_access:
            await self.close(code=4003)
            return

        self.group_name = f"chat_{self.channel_id}"
        self.user = user
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")
        try:
            if msg_type == "message.send":
                await self._handle_send(content)
            elif msg_type == "typing":
                await self._handle_typing(content)
            elif msg_type == "reaction.toggle":
                await self._handle_reaction(content)
        except Exception:  # noqa: BLE001 - never let a bad client payload kill the socket
            await self.send_json({"type": "error", "detail": "Could not process that request."})

    async def _handle_send(self, content):
        channel = await database_sync_to_async(ChannelRepository().get_by_id)(self.channel_id)
        message = await database_sync_to_async(MessageService().send_message)(
            channel=channel, sender=self.user, content=content.get("content", "")
        )
        serialized = await database_sync_to_async(lambda: to_json_safe(MessageSerializer(message).data))()
        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "message": serialized}
        )

    async def _handle_typing(self, content):
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.typing",
                "payload": {"user_id": str(self.user.id), "name": self.user.full_name},
            },
        )

    async def _handle_reaction(self, content):
        message = await database_sync_to_async(MessageRepository().get_by_id)(content.get("message_id"))
        if message is None or str(message.channel_id) != str(self.channel_id):
            return
        result = await database_sync_to_async(MessageService().toggle_reaction)(
            message=message, user=self.user, emoji=content.get("emoji", "")
        )
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.reaction", "payload": {"message_id": str(message.id), **result}},
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message.created", "message": event["message"]})

    async def chat_typing(self, event):
        await self.send_json({"type": "typing", **event["payload"]})

    async def chat_reaction(self, event):
        await self.send_json({"type": "reaction.updated", **event["payload"]})
