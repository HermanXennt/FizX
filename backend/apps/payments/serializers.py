from rest_framework import serializers

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "status",
            "is_active",
            "current_period_end",
            "cancel_at_period_end",
            "created_at",
        )
        read_only_fields = fields


class CreateCheckoutSessionSerializer(serializers.Serializer):
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()


class CreatePortalSessionSerializer(serializers.Serializer):
    return_url = serializers.URLField()
