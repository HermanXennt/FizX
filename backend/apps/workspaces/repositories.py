from django.db import models

from apps.core.repositories import BaseRepository

from .models import Invitation, InvitationStatus, Workspace, WorkspaceMember, WorkspaceRole


class WorkspaceRepository(BaseRepository[Workspace]):
    model = Workspace

    def for_user(self, user):
        return self.get_queryset().filter(membership_set__user=user).distinct()


class WorkspaceMemberRepository(BaseRepository[WorkspaceMember]):
    model = WorkspaceMember

    def get_membership(self, workspace, user) -> WorkspaceMember | None:
        return self.get_queryset().filter(workspace=workspace, user=user).first()

    def owners(self, workspace):
        return self.get_queryset().filter(workspace=workspace, role=WorkspaceRole.OWNER)

    def for_workspace(self, workspace, search: str = ""):
        queryset = self.get_queryset().filter(workspace=workspace).select_related("user")
        if search:
            queryset = queryset.filter(
                models.Q(user__first_name__icontains=search)
                | models.Q(user__last_name__icontains=search)
                | models.Q(user__phone_number__icontains=search)
            )
        return queryset


class InvitationRepository(BaseRepository[Invitation]):
    model = Invitation

    def get_by_token(self, token: str) -> Invitation | None:
        return self.get_queryset().filter(token=token).first()

    def pending_for_workspace(self, workspace):
        return self.get_queryset().filter(workspace=workspace, status=InvitationStatus.PENDING)

    def pending_for_phone_number(self, workspace, phone_number: str) -> Invitation | None:
        return self.get_queryset().filter(
            workspace=workspace, phone_number=phone_number, status=InvitationStatus.PENDING
        ).first()
