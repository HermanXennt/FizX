from rest_framework import serializers

PRESET_CHOICES = ["summarize", "action_items", "follow_up_email", "who_hasnt_spoken"]


class AskAiSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True, default="")
    preset = serializers.ChoiceField(choices=PRESET_CHOICES, required=False, allow_blank=True, default="")
    meeting_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        if not attrs.get("message") and not attrs.get("preset"):
            raise serializers.ValidationError("Either message or preset is required.")
        return attrs


class AskAiResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
