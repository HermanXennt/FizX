from apps.core.repositories import BaseRepository

from .models import User


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.get_queryset().filter(email__iexact=email).first()

    def email_exists(self, email: str) -> bool:
        return self.get_queryset().filter(email__iexact=email).exists()
