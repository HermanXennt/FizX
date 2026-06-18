from rest_framework import serializers

from apps.users.serializers import PublicUserSerializer

from .models import Meeting, MeetingParticipant, ParticipantRole


class MeetingSerializer(serializers.ModelSerializer):
    host = PublicUserSerializer(read_only=True)
    requires_password = serializers.BooleanField(read_only=True)
    is_recurring_template = serializers.BooleanField(read_only=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = (
            "id",
            "workspace",
            "host",
            "title",
            "description",
            "room_name",
            "status",
            "requires_password",
            "waiting_room_enabled",
            "max_participants",
            "scheduled_start",
            "scheduled_end",
            "actual_start",
            "actual_end",
            "recurrence_rule",
            "is_recurring_template",
            "parent_meeting",
            "participant_count",
            "created_at",
        )
        read_only_fields = (
            "id",
            "host",
            "room_name",
            "status",
            "actual_start",
            "actual_end",
            "parent_meeting",
            "created_at",
        )

    def get_participant_count(self, obj: Meeting) -> int:
        return obj.participants.filter(status="admitted").count()


class CreateInstantMeetingSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, default="Instant Meeting")
    workspace = serializers.UUIDField(required=False, allow_null=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list, max_length=50
    )


class ScheduleMeetingSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    workspace = serializers.UUIDField(required=False, allow_null=True)
    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField()
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    waiting_room_enabled = serializers.BooleanField(required=False, default=True)
    max_participants = serializers.IntegerField(required=False, default=100, min_value=2, max_value=1000)
    recurrence_rule = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_workspace(self, value):
        if value is None:
            return None
        from apps.workspaces.models import Workspace

        try:
            return Workspace.objects.get(pk=value)
        except Workspace.DoesNotExist as exc:
            raise serializers.ValidationError("Workspace not found.") from exc


class JoinMeetingSerializer(serializers.Serializer):
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class MeetingParticipantSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = MeetingParticipant
        fields = ("id", "user", "role", "status", "joined_at", "left_at", "is_muted", "hand_raised")
        read_only_fields = fields


class JoinMeetingResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    token = serializers.CharField(allow_null=True)
    livekit_url = serializers.CharField()
    participant = MeetingParticipantSerializer()
    meeting = MeetingSerializer()


class SetHandRaisedSerializer(serializers.Serializer):
    raised = serializers.BooleanField()


class ChangeParticipantRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[ParticipantRole.CO_HOST, ParticipantRole.PARTICIPANT])
