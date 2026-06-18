from django.urls import path

from ..views.profile import AvatarView, MeView, PresenceView

app_name = "users"

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/avatar/", AvatarView.as_view(), name="me-avatar"),
    path("me/presence/", PresenceView.as_view(), name="me-presence"),
]
