from django.urls import path

from ..views.profile import AvatarView, MeView, PresenceView, UserSearchView
from ..views.whatsapp_groups import (
    WhatsAppConnectView,
    WhatsAppDisconnectView,
    WhatsAppGroupsView,
    WhatsAppQrView,
    WhatsAppStatusView,
)

app_name = "users"

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/avatar/", AvatarView.as_view(), name="me-avatar"),
    path("me/presence/", PresenceView.as_view(), name="me-presence"),
    path("search/", UserSearchView.as_view(), name="search"),
    path("me/whatsapp-groups/connect/", WhatsAppConnectView.as_view(), name="me-whatsapp-connect"),
    path("me/whatsapp-groups/disconnect/", WhatsAppDisconnectView.as_view(), name="me-whatsapp-disconnect"),
    path("me/whatsapp-groups/status/", WhatsAppStatusView.as_view(), name="me-whatsapp-status"),
    path("me/whatsapp-groups/qr/", WhatsAppQrView.as_view(), name="me-whatsapp-qr"),
    path("me/whatsapp-groups/groups/", WhatsAppGroupsView.as_view(), name="me-whatsapp-groups"),
]
