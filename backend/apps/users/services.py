from apps.core.exceptions import ValidationError
from apps.integrations.whatsapp_otp import service as whatsapp_otp

from .models import User
from .repositories import UserRepository


class AuthService:
    def __init__(self, repository: UserRepository | None = None):
        self.repository = repository or UserRepository()

    def request_otp(self, *, phone_number: str) -> None:
        whatsapp_otp.send_otp(phone_number=phone_number)

    def verify_otp(
        self, *, phone_number: str, code: str, first_name: str = "", account_type: str = ""
    ) -> tuple[User, bool]:
        """Verifies the WhatsApp OTP and logs in or registers the number.

        Returns (user, created) - created is True the first time this phone
        number completes verification, since that's the only signal that
        distinguishes "registration" from "login" in a passwordless flow.
        """
        if not whatsapp_otp.verify_otp(phone_number=phone_number, code=code):
            raise ValidationError(detail="That code is incorrect or has expired.")

        user = self.repository.get_by_phone_number(phone_number)
        if user is not None:
            return user, False

        if not first_name.strip():
            raise ValidationError(detail="first_name is required to create a new account.")
        if not account_type:
            raise ValidationError(detail="account_type is required to create a new account.")

        user = User.objects.create_user(
            phone_number=phone_number, first_name=first_name.strip(), account_type=account_type
        )
        return user, True


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
