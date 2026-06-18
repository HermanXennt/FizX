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

    def for_workspace(self, workspace):
        return self.get_queryset().filter(workspace=workspace).select_related("user")


class InvitationRepository(BaseRepository[Invitation]):
    model = Invitation

    def get_by_token(self, token: str) -> Invitation | None:
        return self.get_queryset().filter(token=token).first()

    def pending_for_workspace(self, workspace):
        return self.get_queryset().filter(workspace=workspace, status=InvitationStatus.PENDING)

    def pending_for_email(self, workspace, email: str) -> Invitation | None:
        return self.get_queryset().filter(
            workspace=workspace, email__iexact=email, status=InvitationStatus.PENDING
        ).first()
