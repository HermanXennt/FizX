from rest_framework import serializers

from .models import AnalyticsEventType


class DayCountSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class TopHostSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    name = serializers.CharField()
    meeting_count = serializers.IntegerField()


class WorkspaceOverviewSerializer(serializers.Serializer):
    total_meetings = serializers.IntegerField()
    total_meeting_minutes = serializers.FloatField()
    avg_meeting_duration_minutes = serializers.FloatField()
    total_recordings = serializers.IntegerField()
    meetings_by_day = DayCountSerializer(many=True)
    top_hosts = TopHostSerializer(many=True)


class StudentRosterEntrySerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    name = serializers.CharField()
    meetings_attended = serializers.IntegerField()
    total_meetings = serializers.IntegerField()
    total_minutes = serializers.FloatField()
    last_attended = serializers.DateTimeField(allow_null=True)


class UserStatsSerializer(serializers.Serializer):
    meetings_hosted = serializers.IntegerField()
    meetings_attended = serializers.IntegerField()
    total_minutes_in_meetings = serializers.FloatField()
    activity_by_day = DayCountSerializer(many=True)


class LogEventSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=AnalyticsEventType.choices, default=AnalyticsEventType.GENERIC)
    name = serializers.CharField(max_length=100)
    workspace = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, default=dict)
