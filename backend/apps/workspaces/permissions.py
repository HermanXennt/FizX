from rest_framework.permissions import BasePermission

from .models import WorkspaceRole
from .repositories import WorkspaceMemberRepository


def _get_workspace(obj):
    from .models import Workspace

    return obj if isinstance(obj, Workspace) else getattr(obj, "workspace", None)


class IsWorkspaceMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        workspace = _get_workspace(obj)
        if workspace is None or not request.user.is_authenticated:
            return False
        return WorkspaceMemberRepository().get_membership(workspace, request.user) is not None


class IsWorkspaceAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        workspace = _get_workspace(obj)
        if workspace is None or not request.user.is_authenticated:
            return False
        membership = WorkspaceMemberRepository().get_membership(workspace, request.user)
        return membership is not None and membership.role in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN)


class IsWorkspaceOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        workspace = _get_workspace(obj)
        if workspace is None or not request.user.is_authenticated:
            return False
        membership = WorkspaceMemberRepository().get_membership(workspace, request.user)
        return membership is not None and membership.role == WorkspaceRole.OWNER
