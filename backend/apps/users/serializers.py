import re

from rest_framework import serializers

from .models import AccountType, PresenceStatus, User

PHONE_NUMBER_RE = re.compile(r"^\d{7,15}$")


def normalize_phone_number(value: str) -> str:
    digits = re.sub(r"[^\d]", "", value)
    if not PHONE_NUMBER_RE.match(digits):
        raise serializers.ValidationError("Enter a valid phone number, digits only (7-15 digits).")
    return digits


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "full_name",
            "initials",
            "avatar_url",
            "account_type",
            "presence_status",
            "timezone",
            "created_at",
        )
        read_only_fields = ("id", "phone_number", "account_type", "created_at")

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


class RequestOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value: str) -> str:
        return normalize_phone_number(value)


class VerifyOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField(max_length=10)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    account_type = serializers.ChoiceField(
        choices=AccountType.choices, required=False, allow_blank=True, default=""
    )

    def validate_phone_number(self, value: str) -> str:
        return normalize_phone_number(value)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


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
        fields = ("first_name", "last_name", "timezone")
