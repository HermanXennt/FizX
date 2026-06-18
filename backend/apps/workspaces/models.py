import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import BaseModel


def workspace_avatar_path(instance: "Workspace", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"workspace-avatars/{instance.id}/{uuid.uuid4().hex}.{ext}"


def default_workspace_settings() -> dict:
    return {
        "require_meeting_password": False,
        "require_waiting_room": True,
        "allow_recording": True,
    }


class WorkspacePlan(models.TextChoices):
    FREE = "free", "Free"
    PRO = "pro", "Pro"
    ENTERPRISE = "enterprise", "Enterprise"


class Workspace(BaseModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to=workspace_avatar_path, blank=True, null=True)
    plan = models.CharField(max_length=20, choices=WorkspacePlan.choices, default=WorkspacePlan.FREE)
    config = models.JSONField(default=default_workspace_settings, blank=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="WorkspaceMember", related_name="workspaces"
    )

    class Meta:
        db_table = "workspaces"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "workspace"
            slug = base_slug
            counter = 1
            while Workspace.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)


class WorkspaceRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"


class WorkspaceMember(BaseModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="membership_set")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspace_memberships")
    role = models.CharField(max_length=20, choices=WorkspaceRole.choices, default=WorkspaceRole.MEMBER)

    class Meta:
        db_table = "workspace_members"
        constraints = [
            models.UniqueConstraint(fields=["workspace", "user"], name="unique_workspace_member"),
        ]
        ordering = ["-role", "created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.workspace.name} ({self.role})"


class InvitationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    REVOKED = "revoked", "Revoked"
    EXPIRED = "expired", "Expired"


def default_invitation_expiry():
    return timezone.now() + timezone.timedelta(days=7)


def generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)


class Invitation(BaseModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(
        max_length=20, choices=[(WorkspaceRole.ADMIN, "Admin"), (WorkspaceRole.MEMBER, "Member")],
        default=WorkspaceRole.MEMBER,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_invitations"
    )
    token = models.CharField(max_length=64, unique=True, default=generate_invitation_token)
    status = models.CharField(max_length=20, choices=InvitationStatus.choices, default=InvitationStatus.PENDING)
    expires_at = models.DateTimeField(default=default_invitation_expiry)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "workspace_invitations"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "email"],
                condition=models.Q(status=InvitationStatus.PENDING),
                name="unique_pending_invite_per_workspace_email",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invite {self.email} -> {self.workspace.name} ({self.status})"

    @property
    def is_expired(self) -> bool:
        return self.status == InvitationStatus.PENDING and timezone.now() > self.expires_at
