from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError

from .models import Channel, ChannelType, Message, MessageReaction
from .repositories import ChannelRepository, MessageReactionRepository, MessageRepository


class ChatAccessService:
    """Centralizes the "can this user read/write this channel" check so the REST
    views and the async WebSocket consumer enforce exactly the same rule."""

    def user_has_access(self, *, channel: Channel, user) -> bool:
        if channel.type == ChannelType.WORKSPACE:
            from apps.workspaces.repositories import WorkspaceMemberRepository

            return WorkspaceMemberRepository().get_membership(channel.workspace, user) is not None

        from apps.meetings.models import ParticipantStatus
        from apps.meetings.repositories import MeetingParticipantRepository

        if channel.meeting.host_id == user.id:
            return True
        participant = MeetingParticipantRepository().get_for_meeting_and_user(channel.meeting, user)
        return participant is not None and participant.status == ParticipantStatus.ADMITTED


class ChannelService:
    def __init__(self, channel_repo: ChannelRepository | None = None):
        self.channel_repo = channel_repo or ChannelRepository()

    def get_or_create_meeting_channel(self, meeting) -> Channel:
        # get_or_create (not check-then-create) so two participants opening
        # chat on the same meeting at once can't both pass the "doesn't exist
        # yet" check and then race to insert - the loser's IntegrityError is
        # caught internally and it re-fetches the winner's row instead.
        channel, _ = Channel.objects.get_or_create(type=ChannelType.MEETING, meeting=meeting)
        return channel

    def get_or_create_workspace_channel(self, workspace, name: str = "general") -> Channel:
        channel, _ = Channel.objects.get_or_create(
            type=ChannelType.WORKSPACE, workspace=workspace, name=name
        )
        return channel


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository | None = None,
        reaction_repo: MessageReactionRepository | None = None,
    ):
        self.message_repo = message_repo or MessageRepository()
        self.reaction_repo = reaction_repo or MessageReactionRepository()

    @transaction.atomic
    def send_message(
        self, *, channel: Channel, sender, content: str = "", attachment=None, reply_to: Message | None = None
    ) -> Message:
        if not content and not attachment:
            raise ValidationError(detail="A message needs content or an attachment.")
        if reply_to is not None and reply_to.channel_id != channel.id:
            raise ValidationError(detail="Cannot reply to a message from another channel.")

        return Message.objects.create(
            channel=channel, sender=sender, content=content, attachment=attachment, reply_to=reply_to
        )

    def edit_message(self, *, message: Message, user, content: str) -> Message:
        if message.sender_id != user.id:
            raise PermissionDeniedError(detail="You can only edit your own messages.")
        if message.is_deleted:
            raise ValidationError(detail="Cannot edit a deleted message.")
        if not content:
            raise ValidationError(detail="Message content cannot be empty.")
        message.content = content
        message.edited_at = timezone.now()
        message.save(update_fields=["content", "edited_at", "updated_at"])
        return message

    def delete_message(self, *, message: Message, user) -> Message:
        if message.sender_id != user.id:
            raise PermissionDeniedError(detail="You can only delete your own messages.")
        message.content = ""
        message.attachment = None
        message.deleted_at = timezone.now()
        message.save(update_fields=["content", "attachment", "deleted_at", "updated_at"])
        return message

    def toggle_reaction(self, *, message: Message, user, emoji: str) -> dict:
        existing = self.reaction_repo.get(message, user, emoji)
        if existing:
            self.reaction_repo.delete(existing)
            return {"added": False, "emoji": emoji}
        MessageReaction.objects.create(message=message, user=user, emoji=emoji)
        return {"added": True, "emoji": emoji}

    def get_message_in_channel_or_raise(self, *, channel: Channel, message_id) -> Message:
        message = self.message_repo.get_by_id(message_id)
        if message is None or message.channel_id != channel.id:
            raise NotFoundError(detail="Message not found in this channel.")
        return message
