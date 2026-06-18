"""Aggregates websocket URL patterns from every app that defines real-time consumers."""

from apps.chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from apps.notifications.routing import websocket_urlpatterns as notifications_websocket_urlpatterns

websocket_urlpatterns = [
    *chat_websocket_urlpatterns,
    *notifications_websocket_urlpatterns,
]
