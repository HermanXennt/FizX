import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ConflictError, ExternalServiceError, ValidationError

from .models import Subscription, SubscriptionStatus
from .repositories import PaymentEventRepository, SubscriptionRepository

logger = logging.getLogger("apps.payments")

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeBillingService:
    def __init__(self, repository: SubscriptionRepository | None = None):
        self.repository = repository or SubscriptionRepository()

    def _get_or_create_local_subscription(self, *, workspace) -> Subscription:
        subscription = self.repository.get_for_workspace(workspace)
        if subscription is not None:
            return subscription

        try:
            customer = stripe.Customer.create(
                name=workspace.name,
                metadata={"workspace_id": str(workspace.id)},
            )
        except stripe.StripeError as exc:
            logger.exception("Stripe Customer.create failed for workspace %s", workspace.id)
            raise ExternalServiceError(detail="Could not set up billing for this workspace.") from exc

        return Subscription.objects.create(workspace=workspace, stripe_customer_id=customer.id)

    def create_checkout_session(self, *, workspace, success_url: str, cancel_url: str) -> str:
        if not settings.STRIPE_PRICE_ID_PRO:
            raise ValidationError(detail="Billing is not configured on this server.")

        subscription = self._get_or_create_local_subscription(workspace=workspace)
        if subscription.is_active:
            raise ConflictError(detail="This workspace already has an active subscription.")

        try:
            session = stripe.checkout.Session.create(
                customer=subscription.stripe_customer_id,
                mode="subscription",
                line_items=[{"price": settings.STRIPE_PRICE_ID_PRO, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"workspace_id": str(workspace.id)},
            )
        except stripe.StripeError as exc:
            logger.exception("Stripe checkout.Session.create failed for workspace %s", workspace.id)
            raise ExternalServiceError(detail="Could not start the checkout session.") from exc

        return session.url

    def create_billing_portal_session(self, *, workspace, return_url: str) -> str:
        subscription = self.repository.get_for_workspace(workspace)
        if subscription is None:
            raise ValidationError(detail="This workspace has no billing account yet.")

        try:
            session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id, return_url=return_url
            )
        except stripe.StripeError as exc:
            logger.exception("Stripe billing_portal.Session.create failed for workspace %s", workspace.id)
            raise ExternalServiceError(detail="Could not open the billing portal.") from exc

        return session.url

    def cancel_subscription(self, *, workspace) -> Subscription:
        subscription = self.repository.get_for_workspace(workspace)
        if subscription is None or not subscription.stripe_subscription_id:
            raise ValidationError(detail="This workspace has no active subscription.")

        try:
            stripe.Subscription.modify(subscription.stripe_subscription_id, cancel_at_period_end=True)
        except stripe.StripeError as exc:
            logger.exception("Stripe Subscription.modify failed for %s", subscription.stripe_subscription_id)
            raise ExternalServiceError(detail="Could not cancel the subscription.") from exc

        subscription.cancel_at_period_end = True
        subscription.save(update_fields=["cancel_at_period_end", "updated_at"])
        return subscription

    @transaction.atomic
    def apply_webhook_event(self, *, event: stripe.Event) -> None:
        from .models import PaymentEvent

        if PaymentEventRepository().already_processed(event.id):
            logger.info("Stripe event %s already processed, skipping", event.id)
            return

        payment_event, _ = PaymentEvent.objects.get_or_create(
            stripe_event_id=event.id, defaults={"type": event.type, "payload": event.to_dict()}
        )

        handler = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_updated,
        }.get(event.type)

        if handler:
            handler(event)

        payment_event.processed_at = timezone.now()
        payment_event.save(update_fields=["processed_at", "updated_at"])

    def _handle_checkout_completed(self, event: stripe.Event) -> None:
        session = event.data.object
        subscription = self.repository.get_by_stripe_customer_id(session.customer)
        if subscription is None:
            logger.warning("checkout.session.completed for unknown customer %s", session.customer)
            return
        subscription.stripe_subscription_id = session.subscription or ""
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.save(update_fields=["stripe_subscription_id", "status", "updated_at"])

        from apps.workspaces.models import WorkspacePlan

        self.repository.update(subscription.workspace, plan=WorkspacePlan.PRO)

    def _handle_subscription_updated(self, event: stripe.Event) -> None:
        stripe_subscription = event.data.object
        subscription = self.repository.get_by_stripe_subscription_id(stripe_subscription.id)
        if subscription is None:
            subscription = self.repository.get_by_stripe_customer_id(stripe_subscription.customer)
        if subscription is None:
            logger.warning("subscription event for unknown subscription %s", stripe_subscription.id)
            return

        subscription.stripe_subscription_id = stripe_subscription.id
        subscription.status = stripe_subscription.status
        subscription.cancel_at_period_end = bool(stripe_subscription.cancel_at_period_end)
        period_end = getattr(stripe_subscription, "current_period_end", None)
        if period_end:
            subscription.current_period_end = timezone.datetime.fromtimestamp(
                period_end, tz=timezone.get_current_timezone()
            )
        subscription.save(
            update_fields=[
                "stripe_subscription_id",
                "status",
                "cancel_at_period_end",
                "current_period_end",
                "updated_at",
            ]
        )

        if not subscription.is_active:
            from apps.workspaces.models import WorkspacePlan

            self.repository.update(subscription.workspace, plan=WorkspacePlan.FREE)
