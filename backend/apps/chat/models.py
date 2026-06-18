import uuid

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class ChannelType(models.TextChoices):
    MEETING = "meeting", "Meeting"
    WORKSPACE = "workspace", "Workspace"


class Channel(BaseModel):
    type = models.CharField(max_length=20, choices=ChannelType.choices)
    name = models.CharField(max_length=100, blank=True)
    workspace = models.ForeignKey(
        "workspaces.Workspace", on_delete=models.CASCADE, null=True, blank=True, related_name="channels"
    )
    meeting = models.OneToOneField(
        "meetings.Meeting", on_delete=models.CASCADE, null=True, blank=True, related_name="chat_channel"
    )

    class Meta:
        db_table = "chat_channels"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(type=ChannelType.WORKSPACE, workspace__isnull=False, meeting__isnull=True)
                    | models.Q(type=ChannelType.MEETING, meeting__isnull=False, workspace__isnull=True)
                ),
                name="channel_exactly_one_parent",
            )
        ]

    def __str__(self) -> str:
        return self.name or f"{self.type} channel"


def message_attachment_path(instance: "Message", filename: str) -> str:
    return f"chat-attachments/{instance.channel_id}/{uuid.uuid4().hex}/{filename}"


class Message(BaseModel):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages")
    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to=message_attachment_path, null=True, blank=True)
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["channel", "created_at"])]

    def __str__(self) -> str:
        return f"{self.sender_id}: {self.content[:30]}"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class MessageReaction(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="message_reactions")
    emoji = models.CharField(max_length=32)

    class Meta:
        db_table = "chat_message_reactions"
        constraints = [
            models.UniqueConstraint(fields=["message", "user", "emoji"], name="unique_message_reaction"),
        ]
        ordering = ["created_at"]
