from apps.core.repositories import BaseRepository

from .models import MeetingRecording


class MeetingRecordingRepository(BaseRepository[MeetingRecording]):
    model = MeetingRecording

    def get_by_egress_id(self, egress_id: str) -> MeetingRecording | None:
        return self.get_queryset().filter(egress_id=egress_id).first()

    def for_meeting(self, meeting):
        return self.get_queryset().filter(meeting=meeting)

    def for_user(self, user):
        from apps.meetings.models import ParticipantStatus

        return self.get_queryset().filter(
            meeting__participants__user=user, meeting__participants__status=ParticipantStatus.ADMITTED
        ).distinct()
