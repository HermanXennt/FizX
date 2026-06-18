from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PresenceStatus, User
from .repositories import UserRepository


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "initials",
            "avatar_url",
            "is_verified",
            "presence_status",
            "timezone",
            "notification_preferences",
            "created_at",
        )
        read_only_fields = ("id", "email", "is_verified", "created_at")

    def get_avatar_url(self, obj: User) -> str | None:
        if not obj.avatar:
            return None
        request = self.context.get("request")
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url


class PublicUserSerializer(serializers.ModelSerializer):
    """Minimal representation safe to expose to other workspace/meeting members."""

    full_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "full_name", "initials", "avatar_url", "presence_status")

    def get_avatar_url(self, obj: User) -> str | None:
        if not obj.avatar:
            return None
        request = self.context.get("request")
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_email(self, value: str) -> str:
        if UserRepository().email_exists(value):
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value


class FizXTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extends SimpleJWT's serializer to embed the user profile in the login response."""

    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user, context=self.context).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value


class EmailVerificationConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField()

    MAX_SIZE_BYTES = 5 * 1024 * 1024

    def validate_avatar(self, value):
        if value.size > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError("Avatar must be smaller than 5MB.")
        if value.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise serializers.ValidationError("Avatar must be a JPEG, PNG, or WEBP image.")
        return value


class PresenceUpdateSerializer(serializers.Serializer):
    presence_status = serializers.ChoiceField(choices=PresenceStatus.choices)


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "timezone", "notification_preferences")
