import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.core.models import BaseModel


def avatar_upload_path(instance: "User", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"avatars/{instance.id}/{uuid.uuid4().hex}.{ext}"


def default_notification_preferences() -> dict:
    return {
        "email_on_invite": True,
        "email_on_meeting_reminder": True,
        "email_on_recording_ready": True,
    }


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class PresenceStatus(models.TextChoices):
    ONLINE = "online", "Online"
    AWAY = "away", "Away"
    DO_NOT_DISTURB = "do_not_disturb", "Do Not Disturb"
    IN_CALL = "in_call", "In a Call"
    OFFLINE = "offline", "Offline"


class AuthProvider(models.TextChoices):
    LOCAL = "local", "Email & Password"
    GOOGLE = "google", "Google"


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)

    auth_provider = models.CharField(max_length=20, choices=AuthProvider.choices, default=AuthProvider.LOCAL)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    presence_status = models.CharField(
        max_length=20, choices=PresenceStatus.choices, default=PresenceStatus.OFFLINE
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    notification_preferences = models.JSONField(
        default=default_notification_preferences,
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email.split("@")[0]

    @property
    def initials(self) -> str:
        parts = [p for p in (self.first_name, self.last_name) if p]
        if parts:
            return "".join(p[0].upper() for p in parts[:2])
        return self.email[:2].upper()
