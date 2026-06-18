from django.contrib import admin

from .models import Channel, Message, MessageReaction


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "name", "workspace", "meeting", "created_at")
    list_filter = ("type",)
    search_fields = ("name",)
    autocomplete_fields = ["workspace", "meeting"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "channel", "sender", "content", "created_at", "deleted_at")
    search_fields = ("content", "sender__email")
    autocomplete_fields = ["channel", "sender", "reply_to"]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ("message", "user", "emoji", "created_at")
    autocomplete_fields = ["message", "user"]
