import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PermissionDeniedError, ValidationError
from apps.integrations.livekit.service import livekit_service
from apps.meetings.permissions import IsMeetingHostOrCoHost, IsMeetingParticipant
from apps.meetings.repositories import MeetingRepository

from .repositories import MeetingRecordingRepository
from .serializers import MeetingRecordingSerializer
from .services import RecordingService

logger = logging.getLogger("apps.recordings")


class MyRecordingsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MeetingRecordingSerializer(many=True)})
    def get(self, request):
        recordings = MeetingRecordingRepository().for_user(request.user).select_related("meeting", "requested_by")[:50]
        return Response(MeetingRecordingSerializer(recordings, many=True).data)


class MeetingRecordingsView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_meeting(self, meeting_id):
        return MeetingRepository().get_by_id_or_raise(meeting_id)

    @extend_schema(responses={200: MeetingRecordingSerializer(many=True)})
    def get(self, request, meeting_id):
        meeting = self._get_meeting(meeting_id)
        if not IsMeetingParticipant().has_object_permission(request, self, meeting):
            raise PermissionDeniedError(detail="You do not have access to this meeting's recordings.")
        recordings = MeetingRecordingRepository().for_meeting(meeting)
        return Response(MeetingRecordingSerializer(recordings, many=True).data)

    @extend_schema(request=None, responses={201: MeetingRecordingSerializer})
    def post(self, request, meeting_id):
        meeting = self._get_meeting(meeting_id)
        if not IsMeetingHostOrCoHost().has_object_permission(request, self, meeting):
            raise PermissionDeniedError(detail="Only the host or co-host can start a recording.")
        recording = RecordingService().start_recording(meeting=meeting, user=request.user)
        return Response(MeetingRecordingSerializer(recording).data, status=status.HTTP_201_CREATED)


class RecordingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_recording(self, request, recording_id):
        recording = MeetingRecordingRepository().get_by_id_or_raise(recording_id)
        if not IsMeetingParticipant().has_object_permission(request, self, recording.meeting):
            raise PermissionDeniedError(detail="You do not have access to this recording.")
        return recording

    @extend_schema(responses={200: MeetingRecordingSerializer})
    def get(self, request, recording_id):
        recording = self._get_recording(request, recording_id)
        return Response(MeetingRecordingSerializer(recording).data)


class StopRecordingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: MeetingRecordingSerializer})
    def post(self, request, recording_id):
        recording = MeetingRecordingRepository().get_by_id_or_raise(recording_id)
        if not IsMeetingHostOrCoHost().has_object_permission(request, self, recording.meeting):
            raise PermissionDeniedError(detail="Only the host or co-host can stop a recording.")
        recording = RecordingService().stop_recording(recording=recording, user=request.user)
        return Response(MeetingRecordingSerializer(recording).data)


class LiveKitEgressWebhookView(APIView):
    """Receives `egress_started` / `egress_updated` / `egress_ended` webhooks from the
    LiveKit Egress service and keeps MeetingRecording rows in sync. Authenticated via
    LiveKit's own Authorization-header JWT signature, not Django session/JWT auth."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        auth_token = request.headers.get("Authorization", "")
        try:
            event = livekit_service.verify_webhook(body=request.body.decode("utf-8"), auth_token=auth_token)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Rejected LiveKit webhook with invalid signature: %s", exc)
            raise ValidationError(detail="Invalid webhook signature.") from exc

        if event.event in ("egress_started", "egress_updated", "egress_ended") and event.egress_info:
            recording = RecordingService().apply_egress_webhook(egress_info=event.egress_info)
            if recording is None:
                logger.info("No matching MeetingRecording for egress %s", event.egress_info.egress_id)

        return Response({"received": True})
