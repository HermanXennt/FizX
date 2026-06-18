from django.db.models import Q

from apps.core.repositories import BaseRepository

from .models import Meeting, MeetingParticipant, ParticipantStatus


class MeetingRepository(BaseRepository[Meeting]):
    model = Meeting

    def get_by_room_name(self, room_name: str) -> Meeting | None:
        return self.get_queryset().filter(room_name=room_name).first()

    def for_user(self, user):
        """Meetings the user hosts or has been invited to/participates in."""
        return self.get_queryset().filter(
            Q(host=user) | Q(participants__user=user)
        ).distinct()


class MeetingParticipantRepository(BaseRepository[MeetingParticipant]):
    model = MeetingParticipant

    def get_for_meeting_and_user(self, meeting, user) -> MeetingParticipant | None:
        return self.get_queryset().filter(meeting=meeting, user=user).first()

    def active_for_meeting(self, meeting):
        return self.get_queryset().filter(
            meeting=meeting, status=ParticipantStatus.ADMITTED
        ).select_related("user")

    def waiting_for_meeting(self, meeting):
        return self.get_queryset().filter(
            meeting=meeting, status=ParticipantStatus.WAITING
        ).select_related("user")

    def for_meeting(self, meeting):
        return self.get_queryset().filter(meeting=meeting).select_related("user")
