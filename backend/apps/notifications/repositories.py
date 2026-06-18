from apps.core.repositories import BaseRepository

from .models import Notification


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def for_user(self, user, unread_only: bool = False):
        queryset = self.get_queryset().filter(recipient=user)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return queryset

    def unread_count(self, user) -> int:
        return self.for_user(user, unread_only=True).count()
