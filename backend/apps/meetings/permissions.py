from rest_framework.permissions import BasePermission

from .models import Meeting, ParticipantRole, ParticipantStatus
from .repositories import MeetingParticipantRepository


def _get_meeting(obj) -> Meeting | None:
    return obj if isinstance(obj, Meeting) else getattr(obj, "meeting", None)


class IsMeetingHostOrCoHost(BasePermission):
    def has_object_permission(self, request, view, obj):
        meeting = _get_meeting(obj)
        if meeting is None or not request.user.is_authenticated:
            return False
        if meeting.host_id == request.user.id:
            return True
        membership = MeetingParticipantRepository().get_for_meeting_and_user(meeting, request.user)
        return (
            membership is not None
            and membership.role in (ParticipantRole.HOST, ParticipantRole.CO_HOST)
            and membership.status == ParticipantStatus.ADMITTED
        )


class IsMeetingParticipant(BasePermission):
    def has_object_permission(self, request, view, obj):
        meeting = _get_meeting(obj)
        if meeting is None or not request.user.is_authenticated:
            return False
        if meeting.host_id == request.user.id:
            return True
        return MeetingParticipantRepository().get_for_meeting_and_user(meeting, request.user) is not None
