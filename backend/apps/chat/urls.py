from django.urls import path

from .views import (
    MeetingChannelDetailView,
    MeetingChannelMessagesView,
    MessageDetailView,
    MessageReactionView,
    WorkspaceChannelDetailView,
    WorkspaceChannelMessagesView,
)

app_name = "chat"

urlpatterns = [
    path("meetings/<uuid:meeting_id>/channel/", MeetingChannelDetailView.as_view(), name="meeting-channel"),
    path("meetings/<uuid:meeting_id>/messages/", MeetingChannelMessagesView.as_view(), name="meeting-messages"),
    path(
        "workspaces/<uuid:workspace_id>/channel/", WorkspaceChannelDetailView.as_view(), name="workspace-channel"
    ),
    path("workspaces/<uuid:workspace_id>/messages/", WorkspaceChannelMessagesView.as_view(), name="workspace-messages"),
    path("messages/<uuid:message_id>/", MessageDetailView.as_view(), name="message-detail"),
    path("messages/<uuid:message_id>/reactions/", MessageReactionView.as_view(), name="message-reactions"),
]
