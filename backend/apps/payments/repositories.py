from apps.core.repositories import BaseRepository

from .models import PaymentEvent, Subscription


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    def get_for_workspace(self, workspace) -> Subscription | None:
        return self.get_queryset().filter(workspace=workspace).first()

    def get_by_stripe_customer_id(self, customer_id: str) -> Subscription | None:
        return self.get_queryset().filter(stripe_customer_id=customer_id).first()

    def get_by_stripe_subscription_id(self, subscription_id: str) -> Subscription | None:
        return self.get_queryset().filter(stripe_subscription_id=subscription_id).first()


class PaymentEventRepository(BaseRepository[PaymentEvent]):
    model = PaymentEvent

    def already_processed(self, stripe_event_id: str) -> bool:
        return self.get_queryset().filter(stripe_event_id=stripe_event_id, processed_at__isnull=False).exists()
