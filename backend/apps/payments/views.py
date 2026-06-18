import logging

import stripe
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PermissionDeniedError, ValidationError
from apps.workspaces.models import WorkspaceRole
from apps.workspaces.repositories import WorkspaceMemberRepository, WorkspaceRepository

from .repositories import SubscriptionRepository
from .serializers import CreateCheckoutSessionSerializer, CreatePortalSessionSerializer, SubscriptionSerializer
from .services import StripeBillingService

logger = logging.getLogger("apps.payments")


def _require_admin(request, workspace):
    membership = WorkspaceMemberRepository().get_membership(workspace, request.user)
    if membership is None or membership.role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
        raise PermissionDeniedError(detail="Only a workspace owner or admin can manage billing.")


class SubscriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: SubscriptionSerializer})
    def get(self, request, workspace_id):
        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        _require_admin(request, workspace)
        subscription = SubscriptionRepository().get_for_workspace(workspace)
        if subscription is None:
            return Response(None)
        return Response(SubscriptionSerializer(subscription).data)


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=CreateCheckoutSessionSerializer, responses={200: None})
    def post(self, request, workspace_id):
        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        _require_admin(request, workspace)
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = StripeBillingService().create_checkout_session(workspace=workspace, **serializer.validated_data)
        return Response({"checkout_url": url})


class CreatePortalSessionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=CreatePortalSessionSerializer, responses={200: None})
    def post(self, request, workspace_id):
        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        _require_admin(request, workspace)
        serializer = CreatePortalSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = StripeBillingService().create_billing_portal_session(workspace=workspace, **serializer.validated_data)
        return Response({"portal_url": url})


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: SubscriptionSerializer})
    def post(self, request, workspace_id):
        workspace = WorkspaceRepository().get_by_id_or_raise(workspace_id)
        _require_admin(request, workspace)
        subscription = StripeBillingService().cancel_subscription(workspace=workspace)
        return Response(SubscriptionSerializer(subscription).data)


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        sig_header = request.headers.get("Stripe-Signature", "")
        try:
            event = stripe.Webhook.construct_event(
                request.body, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (stripe.SignatureVerificationError, ValueError) as exc:
            logger.warning("Rejected Stripe webhook with invalid signature: %s", exc)
            raise ValidationError(detail="Invalid webhook signature.") from exc

        StripeBillingService().apply_webhook_event(event=event)
        return Response({"received": True})
