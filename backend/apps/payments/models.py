from django.db import models

from apps.core.models import BaseModel


class SubscriptionStatus(models.TextChoices):
    INCOMPLETE = "incomplete", "Incomplete"
    TRIALING = "trialing", "Trialing"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past Due"
    CANCELED = "canceled", "Canceled"
    UNPAID = "unpaid", "Unpaid"


class Subscription(BaseModel):
    workspace = models.OneToOneField(
        "workspaces.Workspace", on_delete=models.CASCADE, related_name="subscription"
    )
    stripe_customer_id = models.CharField(max_length=100)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.INCOMPLETE)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)

    class Meta:
        db_table = "subscriptions"

    def __str__(self) -> str:
        return f"{self.workspace.name} subscription ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)


class PaymentEvent(BaseModel):
    """Audit log of processed Stripe webhook events, keyed by Stripe's event id so a
    retried webhook delivery can never be applied twice."""

    stripe_event_id = models.CharField(max_length=120, unique=True)
    type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payment_events"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.type} ({self.stripe_event_id})"
