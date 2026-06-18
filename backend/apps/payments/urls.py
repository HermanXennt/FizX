from django.urls import path

from .views import (
    CancelSubscriptionView,
    CreateCheckoutSessionView,
    CreatePortalSessionView,
    StripeWebhookView,
    SubscriptionDetailView,
)

app_name = "payments"

urlpatterns = [
    path("workspaces/<uuid:workspace_id>/subscription/", SubscriptionDetailView.as_view(), name="subscription"),
    path("workspaces/<uuid:workspace_id>/checkout/", CreateCheckoutSessionView.as_view(), name="checkout"),
    path("workspaces/<uuid:workspace_id>/portal/", CreatePortalSessionView.as_view(), name="portal"),
    path("workspaces/<uuid:workspace_id>/cancel/", CancelSubscriptionView.as_view(), name="cancel"),
    path("webhook/", StripeWebhookView.as_view(), name="webhook"),
]
