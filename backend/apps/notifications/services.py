from django.utils import timezone

from apps.core.exceptions import NotFoundError

from .models import Notification, NotificationType
from .repositories import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository | None = None):
        self.repository = repository or NotificationRepository()

    def create(
        self,
        *,
        recipient,
        type: str = NotificationType.GENERIC,
        title: str,
        body: str = "",
        data: dict | None = None,
    ) -> Notification:
        notification = Notification.objects.create(
            recipient=recipient, type=type, title=title, body=body, data=data or {}
        )
        self._broadcast(notification)
        return notification

    def _broadcast(self, notification: Notification) -> None:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        from apps.core.utils import to_json_safe

        from .serializers import NotificationSerializer

        layer = get_channel_layer()
        if layer is None:
            return
        async_to_sync(layer.group_send)(
            f"notifications_{notification.recipient_id}",
            {
                "type": "notification.message",
                "notification": to_json_safe(NotificationSerializer(notification).data),
            },
        )

    def mark_read(self, *, notification_id, user) -> Notification:
        notification = self.repository.get_by_id(notification_id)
        if notification is None or notification.recipient_id != user.id:
            raise NotFoundError(detail="Notification not found.")
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])
        return notification

    def mark_all_read(self, *, user) -> int:
        return self.repository.for_user(user, unread_only=True).update(is_read=True, read_at=timezone.now())
