from django.contrib import admin

from .models import PaymentEvent, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("workspace", "status", "current_period_end", "cancel_at_period_end", "created_at")
    list_filter = ("status", "cancel_at_period_end")
    search_fields = ("workspace__name", "stripe_customer_id", "stripe_subscription_id")
    autocomplete_fields = ["workspace"]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ("type", "stripe_event_id", "processed_at", "created_at")
    list_filter = ("type",)
    search_fields = ("stripe_event_id",)
    readonly_fields = ("id", "stripe_event_id", "type", "payload", "created_at", "updated_at")
