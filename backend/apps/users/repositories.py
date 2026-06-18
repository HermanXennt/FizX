from apps.core.repositories import BaseRepository

from .models import User


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_phone_number(self, phone_number: str) -> User | None:
        return self.get_queryset().filter(phone_number=phone_number).first()

    def phone_number_exists(self, phone_number: str) -> bool:
        return self.get_queryset().filter(phone_number=phone_number).exists()
