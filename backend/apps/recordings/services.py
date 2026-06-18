import uuid

from django.utils import timezone
from livekit import api as lk_api

from apps.core.exceptions import ConflictError
from apps.integrations.livekit.service import livekit_service

from .models import MeetingRecording, RecordingStatus
from .repositories import MeetingRecordingRepository

_EGRESS_STATUS_MAP = {
    lk_api.EGRESS_STARTING: RecordingStatus.PROCESSING,
    lk_api.EGRESS_ACTIVE: RecordingStatus.PROCESSING,
    lk_api.EGRESS_ENDING: RecordingStatus.PROCESSING,
    lk_api.EGRESS_COMPLETE: RecordingStatus.READY,
    lk_api.EGRESS_FAILED: RecordingStatus.FAILED,
    lk_api.EGRESS_ABORTED: RecordingStatus.FAILED,
    lk_api.EGRESS_LIMIT_REACHED: RecordingStatus.READY,
}


class RecordingService:
    def __init__(self, repository: MeetingRecordingRepository | None = None):
        self.repository = repository or MeetingRecordingRepository()

    def start_recording(self, *, meeting, user) -> MeetingRecording:
        existing = self.repository.for_meeting(meeting).filter(status=RecordingStatus.PROCESSING).first()
        if existing:
            raise ConflictError(detail="A recording is already in progress for this meeting.")

        filepath = f"recordings/{meeting.id}/{uuid.uuid4().hex}.mp4"
        egress_info = livekit_service.start_room_composite_egress(room_name=meeting.room_name, filepath=filepath)

        return MeetingRecording.objects.create(
            meeting=meeting,
            requested_by=user,
            egress_id=egress_info.egress_id,
            status=RecordingStatus.PROCESSING,
            started_at=timezone.now(),
        )

    def stop_recording(self, *, recording: MeetingRecording, user) -> MeetingRecording:
        if recording.status != RecordingStatus.PROCESSING:
            raise ConflictError(detail="This recording is not currently in progress.")
        livekit_service.stop_egress(egress_id=recording.egress_id)
        return recording

    def apply_egress_webhook(self, *, egress_info) -> MeetingRecording | None:
        recording = self.repository.get_by_egress_id(egress_info.egress_id)
        if recording is None:
            return None

        recording.status = _EGRESS_STATUS_MAP.get(egress_info.status, recording.status)
        recording.error_message = egress_info.error or ""

        if egress_info.file_results:
            file_result = egress_info.file_results[0]
            recording.file_url = file_result.location or file_result.filename
            if file_result.duration:
                recording.duration_seconds = int(file_result.duration // 1_000_000_000)
            recording.size_bytes = file_result.size or None

        if recording.status in (RecordingStatus.READY, RecordingStatus.FAILED):
            recording.ended_at = timezone.now()

        recording.save(
            update_fields=[
                "status",
                "error_message",
                "file_url",
                "duration_seconds",
                "size_bytes",
                "ended_at",
                "updated_at",
            ]
        )
        return recording
