from rest_framework import serializers

from apps.users.serializers import PublicUserSerializer, normalize_phone_number

from .models import Invitation, Workspace, WorkspaceMember, WorkspaceRole


class WorkspaceSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "avatar_url",
            "plan",
            "config",
            "member_count",
            "my_role",
            "whatsapp_group_id",
            "whatsapp_group_name",
            "created_at",
        )
        read_only_fields = ("id", "slug", "plan", "whatsapp_group_id", "whatsapp_group_name", "created_at")

    def get_avatar_url(self, obj: Workspace) -> str | None:
        if not obj.avatar:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url

    def get_member_count(self, obj: Workspace) -> int:
        return obj.membership_set.count()

    def get_my_role(self, obj: Workspace) -> str | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.membership_set.filter(user=request.user).first()
        return membership.role if membership else None


class CreateWorkspaceSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(required=False, allow_blank=True, default="")


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)
    # Teammates can see each other's phone number within their own workspace
    # (e.g. to tell two similarly-named people apart when starting a call) -
    # PublicUserSerializer itself stays phone-free since it's also used to
    # represent other participants inside a live meeting, a much wider and
    # less trusted audience.
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ("id", "user", "phone_number", "role", "created_at")
        read_only_fields = fields


class ChangeMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[WorkspaceRole.ADMIN, WorkspaceRole.MEMBER, WorkspaceRole.OWNER])


class InvitationSerializer(serializers.ModelSerializer):
    invited_by = PublicUserSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ("id", "phone_number", "role", "status", "invited_by", "expires_at", "created_at")
        read_only_fields = fields


class CreateInvitationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    role = serializers.ChoiceField(choices=[WorkspaceRole.ADMIN, WorkspaceRole.MEMBER])

    def validate_phone_number(self, value: str) -> str:
        return normalize_phone_number(value)


class ImportWhatsAppGroupSerializer(serializers.Serializer):
    group_id = serializers.CharField()
    group_name = serializers.CharField(required=False, allow_blank=True, default="")
