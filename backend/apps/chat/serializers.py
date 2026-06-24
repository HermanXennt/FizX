from rest_framework import serializers

from apps.users.serializers import PublicUserSerializer

from .models import Channel, Message


class ReactionSummarySerializer(serializers.Serializer):
    emoji = serializers.CharField()
    count = serializers.IntegerField()
    user_ids = serializers.ListField(child=serializers.UUIDField())


class MessageSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer(read_only=True)
    attachment_url = serializers.SerializerMethodField()
    reply_to_id = serializers.PrimaryKeyRelatedField(source="reply_to", read_only=True)
    reactions = serializers.SerializerMethodField()
    is_deleted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "channel",
            "sender",
            "content",
            "attachment_url",
            "attachment_name",
            "attachment_size",
            "attachment_content_type",
            "reply_to_id",
            "reactions",
            "is_deleted",
            "edited_at",
            "created_at",
        )
        read_only_fields = fields

    def get_attachment_url(self, obj: Message) -> str | None:
        if not obj.attachment:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.attachment.url) if request else obj.attachment.url

    def get_reactions(self, obj: Message) -> list:
        summary: dict[str, dict] = {}
        for reaction in obj.reactions.all():
            bucket = summary.setdefault(reaction.emoji, {"emoji": reaction.emoji, "count": 0, "user_ids": []})
            bucket["count"] += 1
            bucket["user_ids"].append(reaction.user_id)
        return list(summary.values())


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=True, default="")
    attachment = serializers.FileField(required=False, allow_null=True)
    reply_to = serializers.UUIDField(required=False, allow_null=True)

    MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024

    def validate_attachment(self, value):
        if value and value.size > self.MAX_ATTACHMENT_BYTES:
            raise serializers.ValidationError("Attachments must be smaller than 25MB.")
        return value


class EditMessageSerializer(serializers.Serializer):
    content = serializers.CharField()


class ToggleReactionSerializer(serializers.Serializer):
    emoji = serializers.CharField(max_length=32)


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ("id", "type", "name", "workspace", "meeting", "created_at")
        read_only_fields = fields
