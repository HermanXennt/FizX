from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.whatsapp_otp import service as whatsapp_otp


class WhatsAppConnectView(APIView):
    """Starts (or resumes) the requesting user's own WhatsApp group session.

    Scoped strictly to request.user.id - a user can only ever drive their
    own session, never anyone else's.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        whatsapp_otp.start_group_session(teacher_id=str(request.user.id))
        return Response({"status": whatsapp_otp.get_group_session_status(teacher_id=str(request.user.id))})


class WhatsAppStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request):
        return Response({"status": whatsapp_otp.get_group_session_status(teacher_id=str(request.user.id))})


class WhatsAppQrView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request):
        qr = whatsapp_otp.get_group_session_qr(teacher_id=str(request.user.id))
        if qr is None:
            return Response({"qr": None}, status=404)
        return Response({"qr": qr})


class WhatsAppGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request):
        groups = whatsapp_otp.list_whatsapp_groups(teacher_id=str(request.user.id))
        return Response({"groups": groups})


class WhatsAppDisconnectView(APIView):
    """Unlinks the requesting user's own WhatsApp session and wipes its stored
    credentials - the undo for WhatsAppConnectView. Does not touch any
    workspace's whatsapp_group_id link; unlinking a specific group's sync is
    a separate action on the workspace itself."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        whatsapp_otp.disconnect_group_session(teacher_id=str(request.user.id))
        return Response({"status": "disconnected"})
