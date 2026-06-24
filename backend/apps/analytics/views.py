from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PermissionDeniedError
from apps.workspaces.repositories import WorkspaceMemberRepository, WorkspaceRepository

from .serializers import (
    LogEventSerializer,
    StudentRosterEntrySerializer,
    UserStatsSerializer,
    WorkspaceOverviewSerializer,
)
from .services import AnalyticsEventService, UserAnalyticsService, WorkspaceAnalyticsService


class WorkspaceOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: WorkspaceOverviewSerializer})
    def get(self, request, workspace_id):
        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        if WorkspaceMemberRepository().get_membership(workspace, request.user) is None:
            raise PermissionDeniedError(detail="You are not a member of this workspace.")
        data = WorkspaceAnalyticsService().get_overview(workspace=workspace)
        return Response(WorkspaceOverviewSerializer(data).data)


class WorkspaceStudentRosterView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: StudentRosterEntrySerializer(many=True)})
    def get(self, request, workspace_id):
        from apps.workspaces.models import WorkspaceRole

        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        membership = WorkspaceMemberRepository().get_membership(workspace, request.user)
        if membership is None or membership.role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            raise PermissionDeniedError(detail="Only a workspace teacher can view the student roster.")
        data = WorkspaceAnalyticsService().get_student_roster(workspace=workspace)
        return Response(StudentRosterEntrySerializer(data, many=True).data)


class MyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserStatsSerializer})
    def get(self, request):
        data = UserAnalyticsService().get_my_stats(user=request.user)
        return Response(UserStatsSerializer(data).data)


class LogEventView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "chat"

    @extend_schema(request=LogEventSerializer, responses={201: None})
    def post(self, request):
        serializer = LogEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        workspace = None
        if data.get("workspace"):
            workspace = WorkspaceRepository().get_by_id_or_raise(data["workspace"])

        AnalyticsEventService().log(
            user=request.user,
            workspace=workspace,
            event_type=data["event_type"],
            name=data["name"],
            metadata=data.get("metadata"),
        )
        return Response(status=status.HTTP_201_CREATED)
