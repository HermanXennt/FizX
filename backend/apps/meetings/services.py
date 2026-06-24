import logging
from datetime import datetime

from dateutil.rrule import rrulestr
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ConflictError, PermissionDeniedError, ValidationError
from apps.integrations.livekit.service import livekit_service

from .models import Meeting, MeetingParticipant, MeetingStatus, ParticipantRole, ParticipantStatus
from .repositories import MeetingParticipantRepository, MeetingRepository

logger = logging.getLogger("apps.meetings")

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
    def create_instant_meeting(
        self, *, host, workspace=None, title: str = "Instant Meeting", participant_ids: list | None = None
    ) -> Meeting:
        from apps.users.models import AccountType

        if host.account_type != AccountType.TEACHER:
            raise PermissionDeniedError(detail="Only teacher accounts can start a call.")

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
        if participant_ids:
            self._invite_participants(meeting=meeting, host=host, user_ids=participant_ids)
        return meeting

    def _invite_participants(self, *, meeting: Meeting, host, user_ids: list) -> None:
        from apps.notifications.models import NotificationType
        from apps.notifications.services import NotificationService
        from apps.users.repositories import UserRepository

        invitees = UserRepository().get_queryset().filter(id__in=user_ids).exclude(id=host.id)
        notification_service = NotificationService()
        for invitee in invitees:
            MeetingParticipant.objects.get_or_create(
                meeting=meeting,
                user=invitee,
                defaults={"role": ParticipantRole.PARTICIPANT, "status": ParticipantStatus.INVITED},
            )
            notification_service.create(
                recipient=invitee,
                type=NotificationType.MEETING_INVITE,
                title=f"{host.full_name} started a call",
                body=meeting.title,
                data={"meeting_id": str(meeting.id), "action_url": f"/call/{meeting.id}"},
            )

    def invite_to_meeting(self, *, meeting: Meeting, host, user_ids: list) -> None:
        if meeting.status != MeetingStatus.LIVE:
            raise ConflictError(detail="Only a live meeting can be joined.")
        self._invite_participants(meeting=meeting, host=host, user_ids=user_ids)

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
        from apps.users.models import AccountType

        if host.account_type != AccountType.TEACHER:
            raise PermissionDeniedError(detail="Only teacher accounts can schedule a call.")
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

        from apps.recordings.models import RecordingStatus
        from apps.recordings.repositories import MeetingRecordingRepository
        from apps.recordings.services import RecordingService

        active_recording = (
            MeetingRecordingRepository().for_meeting(meeting).filter(status=RecordingStatus.PROCESSING).first()
        )
        if active_recording:
            # Stop the egress explicitly before tearing down the room, so a
            # host forgetting to stop the recording still gets a cleanly
            # finalized file instead of leaving it to however LiveKit
            # happens to handle an egress whose room just disappeared.
            RecordingService().stop_recording(recording=active_recording, user=user)

        livekit_service.delete_room(room_name=meeting.room_name)
        meeting.status = MeetingStatus.ENDED
        meeting.actual_end = timezone.now()
        meeting.save(update_fields=["status", "actual_end", "updated_at"])

        self.participant_repo.get_queryset().filter(
            meeting=meeting, status=ParticipantStatus.ADMITTED
        ).update(status=ParticipantStatus.LEFT, left_at=timezone.now())
        return meeting

    @transaction.atomic
    def end_meeting_from_webhook(self, *, room_name: str) -> Meeting | None:
        """Mirrors end_meeting()'s DB-side effects for a room LiveKit has
        already closed on its own (empty_timeout expiring with nobody left
        in it) - there's nothing left to delete server-side, that's exactly
        why this fired, so unlike end_meeting() this never calls delete_room.
        """
        meeting = self.meeting_repo.get_queryset().filter(room_name=room_name, status=MeetingStatus.LIVE).first()
        if meeting is None:
            return None

        from apps.recordings.models import RecordingStatus
        from apps.recordings.repositories import MeetingRecordingRepository
        from apps.recordings.services import RecordingService

        active_recording = (
            MeetingRecordingRepository().for_meeting(meeting).filter(status=RecordingStatus.PROCESSING).first()
        )
        if active_recording:
            # The room is already gone, so LiveKit's own egress teardown has
            # very likely already fired - this is just a safety net in case
            # this webhook beat the egress's own terminal event. stop_egress
            # on an already-stopping egress is a harmless no-op.
            try:
                livekit_service.stop_egress(egress_id=active_recording.egress_id)
            except Exception:  # noqa: BLE001
                logger.warning("stop_egress on room_finished failed for egress %s", active_recording.egress_id, exc_info=True)

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

        if (
            not is_host_or_cohost
            and meeting.status == MeetingStatus.SCHEDULED
            and meeting.scheduled_start
            and timezone.now() < meeting.scheduled_start
        ):
            raise ValidationError(
                detail=f"This meeting hasn't started yet - it's scheduled for "
                f"{meeting.scheduled_start.strftime('%H:%M UTC')}."
            )

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
            can_publish_camera=not participant.camera_disabled,
            can_publish_microphone=not participant.is_muted,
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
            can_publish_camera=not participant.camera_disabled,
            can_publish_microphone=not participant.is_muted,
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

    def set_participant_media(
        self,
        *,
        meeting: Meeting,
        participant: MeetingParticipant,
        mic_enabled: bool | None = None,
        camera_enabled: bool | None = None,
    ) -> MeetingParticipant:
        update_fields = []
        if mic_enabled is not None:
            participant.is_muted = not mic_enabled
            update_fields.append("is_muted")
        if camera_enabled is not None:
            participant.camera_disabled = not camera_enabled
            update_fields.append("camera_disabled")
        if update_fields:
            participant.save(update_fields=[*update_fields, "updated_at"])

        livekit_service.update_participant_permissions(
            room_name=meeting.room_name,
            identity=participant.livekit_identity,
            can_publish_camera=not participant.camera_disabled,
            can_publish_microphone=not participant.is_muted,
        )
        livekit_service.send_data(
            room_name=meeting.room_name,
            payload={
                "event": "media_permissions_changed",
                "mic_enabled": not participant.is_muted,
                "camera_enabled": not participant.camera_disabled,
            },
            topic="meeting-events",
            destination_identities=[participant.livekit_identity],
        )
        return participant

    def sync_participant_permissions(self, *, meeting: Meeting, participant: MeetingParticipant) -> None:
        """Re-applies whatever mic/camera restriction is already persisted for this
        participant - called by the client right after it connects, so a
        reconnect/refresh re-locks promptly even if the JWT-level restriction
        baked in at token-issue time didn't take hold."""
        livekit_service.update_participant_permissions(
            room_name=meeting.room_name,
            identity=participant.livekit_identity,
            can_publish_camera=not participant.camera_disabled,
            can_publish_microphone=not participant.is_muted,
        )

    def set_hand_raised(self, *, meeting: Meeting, participant: MeetingParticipant, raised: bool) -> MeetingParticipant:
        participant.hand_raised = raised
        participant.save(update_fields=["hand_raised", "updated_at"])
        livekit_service.send_data(
            room_name=meeting.room_name,
            payload={"event": "hand_raised" if raised else "hand_lowered", "identity": participant.livekit_identity},
            topic="meeting-events",
        )
        return participant

    def mark_spoken(self, *, participant: MeetingParticipant) -> MeetingParticipant:
        if not participant.has_spoken:
            participant.has_spoken = True
            participant.save(update_fields=["has_spoken", "updated_at"])
        return participant
