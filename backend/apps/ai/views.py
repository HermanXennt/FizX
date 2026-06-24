from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PermissionDeniedError
from apps.meetings.permissions import IsMeetingParticipant
from apps.meetings.models import MeetingStatus
from apps.meetings.repositories import MeetingRepository

from . import services
from .serializers import AskAiResponseSerializer, AskAiSerializer


class AskAiView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=AskAiSerializer, responses={200: AskAiResponseSerializer})
    def post(self, request):
        serializer = AskAiSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        meeting = None
        if data["meeting_id"]:
            meeting = MeetingRepository().get_by_id_or_raise(data["meeting_id"])
            if not IsMeetingParticipant().has_object_permission(request, self, meeting):
                raise PermissionDeniedError(detail="You don't have access to that meeting.")

        user_has_live_meeting = MeetingRepository().for_user(request.user).filter(status=MeetingStatus.LIVE).exists()

        reply = services.ask(
            message=data["message"],
            preset=data["preset"],
            meeting=meeting,
            user_name=request.user.full_name,
            user_has_live_meeting=user_has_live_meeting,
        )
        return Response({"reply": reply})
