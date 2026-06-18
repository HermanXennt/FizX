from datetime import datetime

from dateutil.rrule import rrulestr
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ConflictError, PermissionDeniedError, ValidationError
from apps.integrations.livekit.service import livekit_service

from .models import Meeting, MeetingParticipant, MeetingStatus, ParticipantRole, ParticipantStatus
from .repositories import MeetingParticipantRepository, MeetingRepository

MAX_RECURRING_OCCURRENCES = 52


class MeetingService:
    def __init__(
        self,
        meeting_repo: MeetingRepository | None = None,
        participant_repo: MeetingParticipantRepository | None = None,
    ):
        self.meeting_repo = meeting_repo or MeetingRepository()
        self.participant_repo = participant_repo or MeetingParticipantRepository()

    @transaction.atomic
    def create_instant_meeting(self, *, host, workspace=None, title: str = "Instant Meeting") -> Meeting:
        meeting = Meeting.objects.create(
            host=host,
            workspace=workspace,
            title=title,
            status=MeetingStatus.LIVE,
            actual_start=timezone.now(),
            waiting_room_enabled=False,
        )
        livekit_service.ensure_room(room_name=meeting.room_name, max_participants=meeting.max_participants)
        MeetingParticipant.objects.create(
            meeting=meeting,
            user=host,
            role=ParticipantRole.HOST,
            status=ParticipantStatus.ADMITTED,
            joined_at=timezone.now(),
        )
        return meeting

    @transaction.atomic
    def schedule_meeting(
        self,
        *,
        host,
        title: str,
        scheduled_start: datetime,
        scheduled_end: datetime,
        workspace=None,
        description: str = "",
        password: str | None = None,
        waiting_room_enabled: bool = True,
        max_participants: int = 100,
        recurrence_rule: str = "",
    ) -> Meeting:
        if scheduled_end <= scheduled_start:
            raise ValidationError(detail="scheduled_end must be after scheduled_start.")

        meeting = Meeting(
            host=host,
            workspace=workspace,
            title=title,
            description=description,
            waiting_room_enabled=waiting_room_enabled,
            max_participants=max_participants,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            recurrence_rule=recurrence_rule,
        )
        meeting.set_password(password)
        meeting.full_clean()
        meeting.save()

        MeetingParticipant.objects.create(meeting=meeting, user=host, role=ParticipantRole.HOST)

        if recurrence_rule:
            self._generate_occurrences(meeting)

        return meeting

    def _generate_occurrences(self, template: Meeting) -> list[Meeting]:
        duration = template.scheduled_end - template.scheduled_start
        try:
            rule = rrulestr(template.recurrence_rule, dtstart=template.scheduled_start)
        except ValueError as exc:
            raise ValidationError(detail=f"Invalid recurrence rule: {exc}") from exc

        occurrences = []
        for i, start in enumerate(rule):
            if i == 0:
                continue  # the template row itself is the first occurrence
            if i >= MAX_RECURRING_OCCURRENCES:
                break
            occurrence = Meeting.objects.create(
                host=template.host,
                workspace=template.workspace,
                title=template.title,
                description=template.description,
                waiting_room_enabled=template.waiting_room_enabled,
                max_participants=template.max_participants,
                password_hash=template.password_hash,
                scheduled_start=start,
                scheduled_end=start + duration,
                parent_meeting=template,
            )
            MeetingParticipant.objects.create(
                meeting=occurrence, user=template.host, role=ParticipantRole.HOST
            )
            occurrences.append(occurrence)
        return occurrences

    @transaction.atomic
    def start_meeting(self, *, meeting: Meeting, user) -> Meeting:
        if meeting.status == MeetingStatus.LIVE:
            return meeting
        if meeting.status != MeetingStatus.SCHEDULED:
            raise ConflictError(detail=f"Cannot start a meeting that is {meeting.status}.")

        livekit_service.ensure_room(room_name=meeting.room_name, max_participants=meeting.max_participants)
        meeting.status = MeetingStatus.LIVE
        meeting.actual_start = timezone.now()
        meeting.save(update_fields=["status", "actual_start", "updated_at"])
        return meeting

    @transaction.atomic
    def end_meeting(self, *, meeting: Meeting, user) -> Meeting:
        if meeting.status != MeetingStatus.LIVE:
            raise ConflictError(detail="Only a live meeting can be ended.")

        livekit_service.delete_room(room_name=meeting.room_name)
        meeting.status = MeetingStatus.ENDED
        meeting.actual_end = timezone.now()
        meeting.save(update_fields=["status", "actual_end", "updated_at"])

        self.participant_repo.get_queryset().filter(
            meeting=meeting, status=ParticipantStatus.ADMITTED
        ).update(status=ParticipantStatus.LEFT, left_at=timezone.now())
        return meeting

    def cancel_meeting(self, *, meeting: Meeting, user) -> Meeting:
        if meeting.status != MeetingStatus.SCHEDULED:
            raise ConflictError(detail="Only a scheduled meeting can be cancelled.")
        return self.meeting_repo.update(meeting, status=MeetingStatus.CANCELLED)

    @transaction.atomic
    def join_meeting(self, *, meeting: Meeting, user, password: str | None = None) -> dict:
        if meeting.status in (MeetingStatus.ENDED, MeetingStatus.CANCELLED):
            raise ConflictError(detail=f"This meeting has {meeting.status}.")

        participant = self.participant_repo.get_for_meeting_and_user(meeting, user)
        is_host_or_cohost = (meeting.host_id == user.id) or (
            participant is not None and participant.role in (ParticipantRole.HOST, ParticipantRole.CO_HOST)
        )

        if not is_host_or_cohost and meeting.requires_password and not meeting.check_password(password):
            raise ValidationError(detail="Incorrect meeting password.")

        if meeting.status == MeetingStatus.SCHEDULED:
            self.start_meeting(meeting=meeting, user=meeting.host)
            meeting.refresh_from_db()

        if participant is None:
            participant = MeetingParticipant.objects.create(
                meeting=meeting,
                user=user,
                role=ParticipantRole.HOST if is_host_or_cohost else ParticipantRole.PARTICIPANT,
            )

        if participant.status in (ParticipantStatus.REMOVED, ParticipantStatus.DENIED):
            raise PermissionDeniedError(detail="You are not permitted to join this meeting.")

        needs_waiting_room = meeting.waiting_room_enabled and not is_host_or_cohost
        if needs_waiting_room and participant.status != ParticipantStatus.ADMITTED:
            participant.status = ParticipantStatus.WAITING
            participant.save(update_fields=["status", "updated_at"])
            return {"status": ParticipantStatus.WAITING, "participant": participant, "token": None, "meeting": meeting}

        participant.status = ParticipantStatus.ADMITTED
        participant.joined_at = participant.joined_at or timezone.now()
        participant.save(update_fields=["status", "joined_at", "updated_at"])

        token = livekit_service.generate_access_token(
            room_name=meeting.room_name,
            identity=participant.livekit_identity,
            display_name=user.full_name,
            is_host=participant.role in (ParticipantRole.HOST, ParticipantRole.CO_HOST),
        )
        return {"status": ParticipantStatus.ADMITTED, "participant": participant, "token": token, "meeting": meeting}

    def get_join_token(self, *, meeting: Meeting, participant: MeetingParticipant) -> str:
        if participant.status != ParticipantStatus.ADMITTED:
            raise ConflictError(detail="You have not been admitted to this meeting yet.")
        return livekit_service.generate_access_token(
            room_name=meeting.room_name,
            identity=participant.livekit_identity,
            display_name=participant.user.full_name,
            is_host=participant.role in (ParticipantRole.HOST, ParticipantRole.CO_HOST),
        )

    @transaction.atomic
    def leave_meeting(self, *, meeting: Meeting, user) -> None:
        participant = self.participant_repo.get_for_meeting_and_user(meeting, user)
        if participant is None:
            return
        participant.status = ParticipantStatus.LEFT
        participant.left_at = timezone.now()
        participant.save(update_fields=["status", "left_at", "updated_at"])

    @transaction.atomic
    def admit_participant(self, *, meeting: Meeting, participant: MeetingParticipant) -> MeetingParticipant:
        if participant.status != ParticipantStatus.WAITING:
            raise ConflictError(detail="This participant is not waiting to be admitted.")
        participant.status = ParticipantStatus.ADMITTED
        participant.joined_at = timezone.now()
        participant.save(update_fields=["status", "joined_at", "updated_at"])
        return participant

    def deny_participant(self, *, meeting: Meeting, participant: MeetingParticipant) -> MeetingParticipant:
        if participant.status != ParticipantStatus.WAITING:
            raise ConflictError(detail="This participant is not waiting to be admitted.")
        participant.status = ParticipantStatus.DENIED
        participant.save(update_fields=["status", "updated_at"])
        return participant

    def remove_participant(self, *, meeting: Meeting, participant: MeetingParticipant) -> MeetingParticipant:
        livekit_service.remove_participant(room_name=meeting.room_name, identity=participant.livekit_identity)
        participant.status = ParticipantStatus.REMOVED
        participant.left_at = timezone.now()
        participant.save(update_fields=["status", "left_at", "updated_at"])
        return participant

    def mute_all(self, *, meeting: Meeting, acting_user) -> list[str]:
        acting_participant = self.participant_repo.get_for_meeting_and_user(meeting, acting_user)
        exclude_identity = str(acting_user.id) if acting_participant else None
        muted = livekit_service.mute_all_participants(room_name=meeting.room_name, exclude_identity=exclude_identity)
        self.participant_repo.get_queryset().filter(
            meeting=meeting, status=ParticipantStatus.ADMITTED
        ).exclude(user=acting_user).update(is_muted=True)
        livekit_service.send_data(
            room_name=meeting.room_name, payload={"event": "muted_by_host"}, topic="meeting-events"
        )
        return muted

    def set_hand_raised(self, *, meeting: Meeting, participant: MeetingParticipant, raised: bool) -> MeetingParticipant:
        participant.hand_raised = raised
        participant.save(update_fields=["hand_raised", "updated_at"])
        livekit_service.send_data(
            room_name=meeting.room_name,
            payload={"event": "hand_raised" if raised else "hand_lowered", "identity": participant.livekit_identity},
            topic="meeting-events",
        )
        return participant
