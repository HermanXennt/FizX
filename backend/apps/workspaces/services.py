from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError

from .models import Invitation, InvitationStatus, Workspace, WorkspaceMember, WorkspaceRole
from .repositories import InvitationRepository, WorkspaceMemberRepository, WorkspaceRepository
from .tasks import send_invitation_email_task


class WorkspaceService:
    def __init__(
        self,
        workspace_repo: WorkspaceRepository | None = None,
        member_repo: WorkspaceMemberRepository | None = None,
    ):
        self.workspace_repo = workspace_repo or WorkspaceRepository()
        self.member_repo = member_repo or WorkspaceMemberRepository()

    @transaction.atomic
    def create_workspace(self, *, owner, name: str, description: str = "") -> Workspace:
        workspace = Workspace.objects.create(name=name, description=description)
        WorkspaceMember.objects.create(workspace=workspace, user=owner, role=WorkspaceRole.OWNER)
        return workspace

    def update_workspace(self, *, workspace: Workspace, **fields) -> Workspace:
        return self.workspace_repo.update(workspace, **fields)

    def delete_workspace(self, *, workspace: Workspace) -> None:
        self.workspace_repo.delete(workspace)

    def get_membership_or_raise(self, *, workspace: Workspace, user) -> WorkspaceMember:
        membership = self.member_repo.get_membership(workspace, user)
        if membership is None:
            raise NotFoundError(detail="You are not a member of this workspace.")
        return membership

    def _is_last_owner(self, workspace: Workspace) -> bool:
        return self.member_repo.owners(workspace).count() <= 1

    @transaction.atomic
    def change_member_role(self, *, workspace: Workspace, target_user, new_role: str, acting_user) -> WorkspaceMember:
        if target_user == acting_user:
            raise ValidationError(detail="You cannot change your own role.")

        acting_membership = self.member_repo.get_membership(workspace, acting_user)
        if new_role == WorkspaceRole.OWNER and (acting_membership is None or acting_membership.role != WorkspaceRole.OWNER):
            raise PermissionDeniedError(detail="Only an existing owner can grant ownership.")

        membership = self.member_repo.get_membership(workspace, target_user)
        if membership is None:
            raise NotFoundError(detail="This user is not a member of the workspace.")

        if membership.role == WorkspaceRole.OWNER and new_role != WorkspaceRole.OWNER:
            if self._is_last_owner(workspace):
                raise ConflictError(detail="A workspace must always have at least one owner.")

        return self.member_repo.update(membership, role=new_role)

    @transaction.atomic
    def remove_member(self, *, workspace: Workspace, target_user, acting_user) -> None:
        membership = self.member_repo.get_membership(workspace, target_user)
        if membership is None:
            raise NotFoundError(detail="This user is not a member of the workspace.")

        if membership.role == WorkspaceRole.OWNER:
            raise PermissionDeniedError(detail="The workspace owner cannot be removed. Transfer ownership first.")

        self.member_repo.delete(membership)

    @transaction.atomic
    def leave_workspace(self, *, workspace: Workspace, user) -> None:
        membership = self.get_membership_or_raise(workspace=workspace, user=user)
        if membership.role == WorkspaceRole.OWNER and self._is_last_owner(workspace):
            raise ConflictError(detail="You are the only owner. Transfer ownership before leaving.")
        self.member_repo.delete(membership)


class InvitationService:
    def __init__(
        self,
        invitation_repo: InvitationRepository | None = None,
        member_repo: WorkspaceMemberRepository | None = None,
    ):
        self.invitation_repo = invitation_repo or InvitationRepository()
        self.member_repo = member_repo or WorkspaceMemberRepository()

    @transaction.atomic
    def invite(self, *, workspace: Workspace, email: str, role: str, invited_by) -> Invitation:
        from apps.users.repositories import UserRepository

        email = email.lower()
        if role == WorkspaceRole.OWNER:
            raise ValidationError(detail="Ownership cannot be granted through an invitation.")

        existing_user = UserRepository().get_by_email(email)
        if existing_user and self.member_repo.get_membership(workspace, existing_user):
            raise ConflictError(detail="This person is already a member of the workspace.")

        existing_invite = self.invitation_repo.pending_for_email(workspace, email)
        if existing_invite:
            existing_invite = self.invitation_repo.update(
                existing_invite,
                role=role,
                invited_by=invited_by,
                expires_at=timezone.now() + timezone.timedelta(days=7),
            )
            send_invitation_email_task.delay(str(existing_invite.id))
            return existing_invite

        invitation = Invitation.objects.create(
            workspace=workspace, email=email, role=role, invited_by=invited_by
        )
        send_invitation_email_task.delay(str(invitation.id))
        return invitation

    def revoke(self, *, invitation: Invitation) -> Invitation:
        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError(detail="Only pending invitations can be revoked.")
        return self.invitation_repo.update(invitation, status=InvitationStatus.REVOKED, responded_at=timezone.now())

    @transaction.atomic
    def accept(self, *, token: str, user) -> WorkspaceMember:
        invitation = self.invitation_repo.get_by_token(token)
        if invitation is None:
            raise NotFoundError(detail="This invitation does not exist.")

        if invitation.is_expired:
            self.invitation_repo.update(invitation, status=InvitationStatus.EXPIRED)
            raise ValidationError(detail="This invitation has expired.")

        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError(detail=f"This invitation has already been {invitation.status}.")

        if invitation.email.lower() != user.email.lower():
            raise PermissionDeniedError(detail="This invitation was sent to a different email address.")

        membership, created = WorkspaceMember.objects.get_or_create(
            workspace=invitation.workspace, user=user, defaults={"role": invitation.role}
        )
        self.invitation_repo.update(invitation, status=InvitationStatus.ACCEPTED, responded_at=timezone.now())
        return membership

    def decline(self, *, token: str, user) -> Invitation:
        invitation = self.invitation_repo.get_by_token(token)
        if invitation is None:
            raise NotFoundError(detail="This invitation does not exist.")
        if invitation.email.lower() != user.email.lower():
            raise PermissionDeniedError(detail="This invitation was sent to a different email address.")
        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError(detail=f"This invitation has already been {invitation.status}.")
        return self.invitation_repo.update(invitation, status=InvitationStatus.DECLINED, responded_at=timezone.now())
