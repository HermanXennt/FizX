from apps.core.repositories import BaseRepository

from .models import Channel, Message, MessageReaction


class ChannelRepository(BaseRepository[Channel]):
    model = Channel

    def get_for_meeting(self, meeting) -> Channel | None:
        return self.get_queryset().filter(meeting=meeting).first()

    def get_for_workspace(self, workspace, name: str) -> Channel | None:
        return self.get_queryset().filter(workspace=workspace, name=name).first()


class MessageRepository(BaseRepository[Message]):
    model = Message

    def for_channel(self, channel):
        return (
            self.get_queryset()
            .filter(channel=channel)
            .select_related("sender", "reply_to", "reply_to__sender")
            .prefetch_related("reactions", "reactions__user")
        )


class MessageReactionRepository(BaseRepository[MessageReaction]):
    model = MessageReaction

    def get(self, message, user, emoji) -> MessageReaction | None:
        return self.get_queryset().filter(message=message, user=user, emoji=emoji).first()
