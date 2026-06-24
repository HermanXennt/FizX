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

        # ADMITTED (still in the call) or LEFT (attended, then left normally)
        # both count as "actually attended" - excluding LEFT meant a host's
        # own recording vanished from their list the moment they hung up.
        # INVITED/WAITING/DENIED/REMOVED never actually got into the room.
        return self.get_queryset().filter(
            meeting__participants__user=user,
            meeting__participants__status__in=(ParticipantStatus.ADMITTED, ParticipantStatus.LEFT),
        ).distinct()
