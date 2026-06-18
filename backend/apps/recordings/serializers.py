from rest_framework import serializers

from apps.users.serializers import PublicUserSerializer

from .models import MeetingRecording


class MeetingRecordingSerializer(serializers.ModelSerializer):
    requested_by = PublicUserSerializer(read_only=True)

    class Meta:
        model = MeetingRecording
        fields = (
            "id",
            "meeting",
            "requested_by",
            "status",
            "file_url",
            "duration_seconds",
            "size_bytes",
            "started_at",
            "ended_at",
            "error_message",
            "created_at",
        )
        read_only_fields = fields
