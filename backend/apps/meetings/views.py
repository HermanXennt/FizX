from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from apps.integrations.turn.service import generate_turn_credentials

from .models import MeetingStatus
from .permissions import IsMeetingHostOrCoHost, IsMeetingParticipant
from .repositories import MeetingParticipantRepository, MeetingRepository
from .serializers import (
    ChangeParticipantRoleSerializer,
    CreateInstantMeetingSerializer,
    JoinMeetingResponseSerializer,
    JoinMeetingSerializer,
    MeetingParticipantSerializer,
    MeetingSerializer,
    ScheduleMeetingSerializer,
    SetHandRaisedSerializer,
)
from .services import MeetingService


class MeetingViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingSerializer
    permission_classes = [IsAuthenticated]
    throttle_scope = "meetings"
    filterset_fields = ["status", "workspace"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return MeetingRepository().model.objects.none()
        if self.action in ("join", "retrieve"):
            return MeetingRepository().get_queryset()
        return MeetingRepository().for_user(self.request.user)

    def get_permissions(self):
        if self.action in (
            "update",
            "partial_update",
            "start",
            "end",
            "cancel",
            "mute_all",
            "admit_participant",
            "deny_participant",
            "remove_participant",
            "change_participant_role",
        ):
            return [IsAuthenticated(), IsMeetingHostOrCoHost()]
        if self.action in ("leave", "token", "raise_hand", "participants"):
            return [IsAuthenticated(), IsMeetingParticipant()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        raise PermissionDeniedError(detail="Meetings cannot be deleted. Cancel a scheduled meeting instead.")

    @extend_schema(request=ScheduleMeetingSerializer, responses={201: MeetingSerializer})
    def create(self, request, *args, **kwargs):
        serializer = ScheduleMeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = MeetingService().schedule_meeting(host=request.user, **serializer.validated_data)
        return Response(
            MeetingSerializer(meeting, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        meeting = self.get_object()
        if meeting.status != MeetingStatus.SCHEDULED:
            raise ConflictError(detail="Only a scheduled meeting can be edited.")
        serializer.save()

    @action(detail=False, methods=["post"])
    @extend_schema(request=CreateInstantMeetingSerializer, responses={201: MeetingSerializer})
    def instant(self, request):
        serializer = CreateInstantMeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = None
        if serializer.validated_data.get("workspace"):
            from apps.workspaces.repositories import WorkspaceRepository

            workspace = WorkspaceRepository().get_by_id_or_raise(serializer.validated_data["workspace"])
        meeting = MeetingService().create_instant_meeting(
            host=request.user,
            workspace=workspace,
            title=serializer.validated_data["title"],
            participant_ids=serializer.validated_data.get("participant_ids"),
        )
        return Response(
            MeetingSerializer(meeting, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    @extend_schema(request=None, responses={200: MeetingSerializer})
    def start(self, request, pk=None):
        meeting = MeetingService().start_meeting(meeting=self.get_object(), user=request.user)
        return Response(MeetingSerializer(meeting, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    @extend_schema(request=None, responses={200: MeetingSerializer})
    def end(self, request, pk=None):
        meeting = MeetingService().end_meeting(meeting=self.get_object(), user=request.user)
        return Response(MeetingSerializer(meeting, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    @extend_schema(request=None, responses={200: MeetingSerializer})
    def cancel(self, request, pk=None):
        meeting = MeetingService().cancel_meeting(meeting=self.get_object(), user=request.user)
        return Response(MeetingSerializer(meeting, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    @extend_schema(request=JoinMeetingSerializer, responses={200: JoinMeetingResponseSerializer})
    def join(self, request, pk=None):
        serializer = JoinMeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = MeetingService().join_meeting(
            meeting=self.get_object(), user=request.user, **serializer.validated_data
        )
        return Response(
            {
                "status": result["status"],
                "token": result["token"],
                "livekit_url": settings.LIVEKIT_URL,
                "participant": MeetingParticipantSerializer(result["participant"]).data,
                "meeting": MeetingSerializer(result["meeting"], context=self.get_serializer_context()).data,
            }
        )

    @action(detail=True, methods=["get"])
    @extend_schema(responses={200: JoinMeetingResponseSerializer})
    def token(self, request, pk=None):
        meeting = self.get_object()
        participant = MeetingParticipantRepository().get_for_meeting_and_user(meeting, request.user)
        if participant is None:
            raise NotFoundError(detail="You are not a participant of this meeting.")
        token = MeetingService().get_join_token(meeting=meeting, participant=participant)
        return Response(
            {
                "status": participant.status,
                "token": token,
                "livekit_url": settings.LIVEKIT_URL,
                "participant": MeetingParticipantSerializer(participant).data,
                "meeting": MeetingSerializer(meeting, context=self.get_serializer_context()).data,
            }
        )

    @action(detail=True, methods=["post"])
    @extend_schema(request=None, responses={204: None})
    def leave(self, request, pk=None):
        MeetingService().leave_meeting(meeting=self.get_object(), user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    @extend_schema(responses={200: MeetingParticipantSerializer(many=True)})
    def participants(self, request, pk=None):
        meeting = self.get_object()
        is_host = IsMeetingHostOrCoHost().has_object_permission(request, self, meeting)
        repo = MeetingParticipantRepository()
        queryset = repo.for_meeting(meeting) if is_host else repo.active_for_meeting(meeting)
        return Response(MeetingParticipantSerializer(queryset, many=True).data)

    def _get_participant_or_404(self, meeting, participant_id):
        participant = MeetingParticipantRepository().get_by_id(participant_id)
        if participant is None or participant.meeting_id != meeting.id:
            raise NotFoundError(detail="Participant not found in this meeting.")
        return participant

    @action(detail=True, methods=["post"], url_path=r"participants/(?P<participant_id>[^/.]+)/admit")
    @extend_schema(request=None, responses={200: MeetingParticipantSerializer})
    def admit_participant(self, request, pk=None, participant_id=None):
        meeting = self.get_object()
        participant = self._get_participant_or_404(meeting, participant_id)
        participant = MeetingService().admit_participant(meeting=meeting, participant=participant)
        return Response(MeetingParticipantSerializer(participant).data)

    @action(detail=True, methods=["post"], url_path=r"participants/(?P<participant_id>[^/.]+)/deny")
    @extend_schema(request=None, responses={200: MeetingParticipantSerializer})
    def deny_participant(self, request, pk=None, participant_id=None):
        meeting = self.get_object()
        participant = self._get_participant_or_404(meeting, participant_id)
        participant = MeetingService().deny_participant(meeting=meeting, participant=participant)
        return Response(MeetingParticipantSerializer(participant).data)

    @action(detail=True, methods=["post"], url_path=r"participants/(?P<participant_id>[^/.]+)/remove")
    @extend_schema(request=None, responses={200: MeetingParticipantSerializer})
    def remove_participant(self, request, pk=None, participant_id=None):
        meeting = self.get_object()
        participant = self._get_participant_or_404(meeting, participant_id)
        participant = MeetingService().remove_participant(meeting=meeting, participant=participant)
        return Response(MeetingParticipantSerializer(participant).data)

    @action(detail=True, methods=["patch"], url_path=r"participants/(?P<participant_id>[^/.]+)/role")
    @extend_schema(request=ChangeParticipantRoleSerializer, responses={200: MeetingParticipantSerializer})
    def change_participant_role(self, request, pk=None, participant_id=None):
        meeting = self.get_object()
        participant = self._get_participant_or_404(meeting, participant_id)
        serializer = ChangeParticipantRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant.role = serializer.validated_data["role"]
        participant.save(update_fields=["role", "updated_at"])
        return Response(MeetingParticipantSerializer(participant).data)

    @action(detail=True, methods=["post"])
    @extend_schema(request=None, responses={200: None})
    def mute_all(self, request, pk=None):
        muted = MeetingService().mute_all(meeting=self.get_object(), acting_user=request.user)
        return Response({"muted_identities": muted})

    @action(detail=True, methods=["post"], url_path="hand")
    @extend_schema(request=SetHandRaisedSerializer, responses={200: MeetingParticipantSerializer})
    def raise_hand(self, request, pk=None):
        meeting = self.get_object()
        serializer = SetHandRaisedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = MeetingParticipantRepository().get_for_meeting_and_user(meeting, request.user)
        if participant is None:
            raise NotFoundError(detail="You are not a participant of this meeting.")
        participant = MeetingService().set_hand_raised(
            meeting=meeting, participant=participant, raised=serializer.validated_data["raised"]
        )
        return Response(MeetingParticipantSerializer(participant).data)


class IceServersView(APIView):
    """Returns STUN/TURN server config for the WebRTC client to use as a
    fallback alongside LiveKit's own host candidates. Falling back to a TURN
    relay (coturn) is what keeps calls connected when a direct UDP path
    between two peers is unreliable (restrictive NAT, mobile networks, etc).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request):
        turn_host = request.get_host().split(":")[0]
        ice_servers = [{"urls": ["stun:stun.l.google.com:19302"]}]

        if settings.TURN_SHARED_SECRET:
            turn = generate_turn_credentials(user_identifier=str(request.user.id), turn_host=turn_host)
            ice_servers.append(
                {"urls": turn["urls"], "username": turn["username"], "credential": turn["credential"]}
            )

        return Response({"ice_servers": ice_servers})
