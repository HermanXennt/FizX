import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.core.models import BaseModel


def avatar_upload_path(instance: "User", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"avatars/{instance.id}/{uuid.uuid4().hex}.{ext}"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number: str, **extra_fields):
        if not phone_number:
            raise ValueError("Users must have a phone number.")
        user = self.model(phone_number=phone_number, **extra_fields)
        # Identity is proven by WhatsApp OTP on every login, not a password -
        # this makes the password unusable rather than leaving it empty/None,
        # which Django's auth backend would otherwise treat as a valid match
        # for an empty submitted password.
        user.set_unusable_password()
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_user(self, phone_number: str, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, **extra_fields)

    def create_superuser(self, phone_number: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user


class PresenceStatus(models.TextChoices):
    ONLINE = "online", "Online"
    AWAY = "away", "Away"
    DO_NOT_DISTURB = "do_not_disturb", "Do Not Disturb"
    IN_CALL = "in_call", "In a Call"
    OFFLINE = "offline", "Offline"


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    # Digits only, no leading "+" - the canonical form both the WhatsApp OTP
    # service and Django use, so phone numbers never need reformatting at
    # the boundary between them.
    phone_number = models.CharField(max_length=15, unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    presence_status = models.CharField(
        max_length=20, choices=PresenceStatus.choices, default=PresenceStatus.OFFLINE
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.phone_number

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.phone_number

    @property
    def initials(self) -> str:
        parts = [p for p in (self.first_name, self.last_name) if p]
        if parts:
            return "".join(p[0].upper() for p in parts[:2])
        return self.phone_number[:2]
