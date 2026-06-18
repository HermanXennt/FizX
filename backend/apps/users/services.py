import logging

from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from apps.core.exceptions import ApplicationError, ValidationError

from .models import AuthProvider, User
from .repositories import UserRepository
from .tasks import send_password_reset_email_task, send_verification_email_task
from .tokens import email_verification_token_generator

logger = logging.getLogger("apps.users")


class AuthService:
    def __init__(self, repository: UserRepository | None = None):
        self.repository = repository or UserRepository()

    def register(self, *, email: str, password: str, first_name: str = "", last_name: str = "") -> User:
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        self.send_verification_email(user)
        return user

    def send_verification_email(self, user: User) -> None:
        if user.is_verified:
            return
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token_generator.make_token(user)
        verification_url = f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"
        send_verification_email_task.delay(str(user.id), verification_url)

    def confirm_email_verification(self, *, uid: str, token: str) -> User:
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = self.repository.get_by_id_or_raise(user_id)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValidationError(detail="Invalid verification link.") from exc

        if not email_verification_token_generator.check_token(user, token):
            raise ValidationError(detail="This verification link is invalid or has expired.")

        user.is_verified = True
        user.save(update_fields=["is_verified", "updated_at"])
        return user

    def request_password_reset(self, *, email: str) -> None:
        user = self.repository.get_by_email(email)
        if user is None:
            logger.info("Password reset requested for unknown email %s", email)
            return  # do not leak account existence

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        from django.contrib.auth.tokens import default_token_generator

        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
        send_password_reset_email_task.delay(str(user.id), reset_url)

    def confirm_password_reset(self, *, uid: str, token: str, new_password: str) -> User:
        from django.contrib.auth.tokens import default_token_generator

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = self.repository.get_by_id_or_raise(user_id)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValidationError(detail="Invalid password reset link.") from exc

        if not default_token_generator.check_token(user, token):
            raise ValidationError(detail="This password reset link is invalid or has expired.")

        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        return user

    def change_password(self, *, user: User, old_password: str, new_password: str) -> User:
        if not user.check_password(old_password):
            raise ValidationError(detail="Your current password is incorrect.")
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])
        return user

    def login_with_google(self, *, id_token_str: str) -> User:
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise ApplicationError(detail="Google sign-in is not configured on this server.")

        try:
            payload = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
            )
        except ValueError as exc:
            raise ValidationError(detail="Invalid Google credential.") from exc

        if not payload.get("email_verified", False):
            raise ValidationError(detail="Your Google account email is not verified.")

        email = payload["email"].lower()
        user = self.repository.get_by_email(email)
        if user is None:
            user = User.objects.create_user(
                email=email,
                password=None,
                first_name=payload.get("given_name", ""),
                last_name=payload.get("family_name", ""),
                auth_provider=AuthProvider.GOOGLE,
                is_verified=True,
            )
        elif not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified", "updated_at"])

        return user


class UserService:
    def __init__(self, repository: UserRepository | None = None):
        self.repository = repository or UserRepository()

    def update_profile(self, *, user: User, **fields) -> User:
        return self.repository.update(user, **fields)

    def upload_avatar(self, *, user: User, avatar_file) -> User:
        if user.avatar:
            user.avatar.delete(save=False)
        user.avatar = avatar_file
        user.save(update_fields=["avatar", "updated_at"])
        return user

    def remove_avatar(self, *, user: User) -> User:
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=["avatar", "updated_at"])
        return user

    def update_presence(self, *, user: User, presence_status: str) -> User:
        from django.utils import timezone

        user.presence_status = presence_status
        user.last_seen_at = timezone.now()
        user.save(update_fields=["presence_status", "last_seen_at", "updated_at"])
        return user
