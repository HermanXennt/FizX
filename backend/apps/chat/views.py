from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PermissionDeniedError
from apps.core.utils import to_json_safe

from .repositories import MessageRepository
from .serializers import (
    ChannelSerializer,
    EditMessageSerializer,
    MessageSerializer,
    SendMessageSerializer,
    ToggleReactionSerializer,
)
from .services import ChannelService, ChatAccessService, MessageService


class BaseChannelMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "chat"

    def get_channel(self, request, **kwargs):
        raise NotImplementedError

    @extend_schema(responses={200: MessageSerializer(many=True)})
    def get(self, request, **kwargs):
        channel = self.get_channel(request, **kwargs)
        if not ChatAccessService().user_has_access(channel=channel, user=request.user):
            raise PermissionDeniedError(detail="You do not have access to this chat.")
        messages = MessageRepository().for_channel(channel)
        return Response(MessageSerializer(messages, many=True, context={"request": request}).data)

    @extend_schema(request=SendMessageSerializer, responses={201: MessageSerializer})
    def post(self, request, **kwargs):
        channel = self.get_channel(request, **kwargs)
        if not ChatAccessService().user_has_access(channel=channel, user=request.user):
            raise PermissionDeniedError(detail="You do not have access to this chat.")

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        reply_to = None
        if data.get("reply_to"):
            reply_to = MessageService().get_message_in_channel_or_raise(channel=channel, message_id=data["reply_to"])

        message = MessageService().send_message(
            channel=channel,
            sender=request.user,
            content=data.get("content", ""),
            attachment=data.get("attachment"),
            reply_to=reply_to,
        )
        self._broadcast(channel, message, request)
        return Response(
            MessageSerializer(message, context={"request": request}).data, status=status.HTTP_201_CREATED
        )

    def _broadcast(self, channel, message, request):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer is None:
            return
        data = MessageSerializer(message, context={"request": request}).data
        async_to_sync(layer.group_send)(
            f"chat_{channel.id}", {"type": "chat.message", "message": to_json_safe(data)}
        )


class MeetingChannelMessagesView(BaseChannelMessagesView):
    def get_channel(self, request, meeting_id=None, **kwargs):
        from apps.meetings.repositories import MeetingRepository

        meeting = MeetingRepository().get_by_id_or_raise(meeting_id)
        return ChannelService().get_or_create_meeting_channel(meeting)


class WorkspaceChannelMessagesView(BaseChannelMessagesView):
    def get_channel(self, request, workspace_id=None, **kwargs):
        from apps.workspaces.repositories import WorkspaceRepository

        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        return ChannelService().get_or_create_workspace_channel(workspace)


class BaseChannelDetailView(APIView):
    """Exposes the channel id for a meeting/workspace so the frontend can open
    the WebSocket connection before any messages exist yet."""

    permission_classes = [IsAuthenticated]

    def get_channel(self, request, **kwargs):
        raise NotImplementedError

    @extend_schema(responses={200: ChannelSerializer})
    def get(self, request, **kwargs):
        channel = self.get_channel(request, **kwargs)
        if not ChatAccessService().user_has_access(channel=channel, user=request.user):
            raise PermissionDeniedError(detail="You do not have access to this chat.")
        return Response(ChannelSerializer(channel).data)


class MeetingChannelDetailView(BaseChannelDetailView):
    def get_channel(self, request, meeting_id=None, **kwargs):
        from apps.meetings.repositories import MeetingRepository

        meeting = MeetingRepository().get_by_id_or_raise(meeting_id)
        return ChannelService().get_or_create_meeting_channel(meeting)


class WorkspaceChannelDetailView(BaseChannelDetailView):
    def get_channel(self, request, workspace_id=None, **kwargs):
        from apps.workspaces.repositories import WorkspaceRepository

        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        return ChannelService().get_or_create_workspace_channel(workspace)


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "chat"

    def _get_message(self, request, message_id):
        message = MessageRepository().get_by_id_or_raise(message_id)
        if not ChatAccessService().user_has_access(channel=message.channel, user=request.user):
            raise PermissionDeniedError(detail="You do not have access to this chat.")
        return message

    @extend_schema(request=EditMessageSerializer, responses={200: MessageSerializer})
    def patch(self, request, message_id):
        message = self._get_message(request, message_id)
        serializer = EditMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = MessageService().edit_message(message=message, user=request.user, **serializer.validated_data)
        return Response(MessageSerializer(message, context={"request": request}).data)

    @extend_schema(request=None, responses={200: MessageSerializer})
    def delete(self, request, message_id):
        message = self._get_message(request, message_id)
        message = MessageService().delete_message(message=message, user=request.user)
        return Response(MessageSerializer(message, context={"request": request}).data)


class MessageReactionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "chat"

    @extend_schema(request=ToggleReactionSerializer, responses={200: None})
    def post(self, request, message_id):
        message = MessageRepository().get_by_id_or_raise(message_id)
        if not ChatAccessService().user_has_access(channel=message.channel, user=request.user):
            raise PermissionDeniedError(detail="You do not have access to this chat.")

        serializer = ToggleReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = MessageService().toggle_reaction(message=message, user=request.user, **serializer.validated_data)
        return Response(result)
