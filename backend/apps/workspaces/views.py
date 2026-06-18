from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import NotFoundError, ValidationError

from .permissions import IsWorkspaceAdminOrOwner, IsWorkspaceMember, IsWorkspaceOwner
from .repositories import InvitationRepository, WorkspaceMemberRepository, WorkspaceRepository
from .serializers import (
    ChangeMemberRoleSerializer,
    CreateInvitationSerializer,
    CreateWorkspaceSerializer,
    InvitationSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSerializer,
)
from .services import InvitationService, WorkspaceService


class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return WorkspaceRepository().model.objects.none()
        return WorkspaceRepository().for_user(self.request.user)

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsWorkspaceOwner()]
        if self.action in (
            "update",
            "partial_update",
            "invitations",
            "member_detail",
            "revoke_invitation",
        ):
            return [IsAuthenticated(), IsWorkspaceAdminOrOwner()]
        if self.action in ("retrieve", "members", "leave"):
            return [IsAuthenticated(), IsWorkspaceMember()]
        return super().get_permissions()

    @extend_schema(request=CreateWorkspaceSerializer, responses={201: WorkspaceSerializer})
    def create(self, request, *args, **kwargs):
        serializer = CreateWorkspaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = WorkspaceService().create_workspace(owner=request.user, **serializer.validated_data)
        return Response(
            WorkspaceSerializer(workspace, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_destroy(self, instance):
        WorkspaceService().delete_workspace(workspace=instance)

    @action(detail=True, methods=["get"])
    @extend_schema(responses={200: WorkspaceMemberSerializer(many=True)})
    def members(self, request, pk=None):
        workspace = self.get_object()
        search = request.query_params.get("q", "")
        members = WorkspaceMemberRepository().for_workspace(workspace, search=search)
        return Response(WorkspaceMemberSerializer(members, many=True).data)

    @action(detail=True, methods=["patch", "delete"], url_path=r"members/(?P<user_id>[^/.]+)")
    @extend_schema(request=ChangeMemberRoleSerializer, responses={200: WorkspaceMemberSerializer})
    def member_detail(self, request, pk=None, user_id=None):
        workspace = self.get_object()
        from apps.users.repositories import UserRepository

        target_user = UserRepository().get_by_id(user_id)
        if target_user is None:
            raise NotFoundError(detail="User not found.")

        if request.method == "PATCH":
            serializer = ChangeMemberRoleSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            membership = WorkspaceService().change_member_role(
                workspace=workspace,
                target_user=target_user,
                new_role=serializer.validated_data["role"],
                acting_user=request.user,
            )
            return Response(WorkspaceMemberSerializer(membership).data)

        WorkspaceService().remove_member(workspace=workspace, target_user=target_user, acting_user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    @extend_schema(request=None, responses={204: None})
    def leave(self, request, pk=None):
        workspace = self.get_object()
        WorkspaceService().leave_workspace(workspace=workspace, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "post"])
    def invitations(self, request, pk=None):
        workspace = self.get_object()
        if request.method == "POST":
            serializer = CreateInvitationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            invitation = InvitationService().invite(
                workspace=workspace, invited_by=request.user, **serializer.validated_data
            )
            return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

        invitations = InvitationRepository().pending_for_workspace(workspace)
        return Response(InvitationSerializer(invitations, many=True).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"invitations/(?P<invitation_id>[^/.]+)/revoke",
    )
    @extend_schema(request=None, responses={200: None})
    def revoke_invitation(self, request, pk=None, invitation_id=None):
        workspace = self.get_object()
        invitation = InvitationRepository().get_by_id_or_raise(invitation_id)
        if invitation.workspace_id != workspace.id:
            raise NotFoundError(detail="This invitation does not belong to this workspace.")
        InvitationService().revoke(invitation=invitation)
        return Response({"detail": "Invitation revoked."})


class InvitationAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: WorkspaceMemberSerializer})
    def post(self, request, token):
        membership = InvitationService().accept(token=token, user=request.user)
        return Response(WorkspaceMemberSerializer(membership).data)


class InvitationDeclineView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: InvitationSerializer})
    def post(self, request, token):
        invitation = InvitationService().decline(token=token, user=request.user)
        return Response(InvitationSerializer(invitation).data)


class InvitationPreviewView(APIView):
    """Lets an unauthenticated visitor see what workspace/role an invite link is for
    before they sign up or log in."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: InvitationSerializer})
    def get(self, request, token):
        invitation = InvitationRepository().get_by_token(token)
        if invitation is None:
            raise NotFoundError(detail="This invitation does not exist.")
        if invitation.is_expired:
            raise ValidationError(detail="This invitation has expired.")
        return Response(InvitationSerializer(invitation).data)
