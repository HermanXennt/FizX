from django.urls import path

from .views import LogEventView, MyStatsView, WorkspaceOverviewView, WorkspaceStudentRosterView

app_name = "analytics"

urlpatterns = [
    path("workspaces/<uuid:workspace_id>/overview/", WorkspaceOverviewView.as_view(), name="workspace-overview"),
    path("workspaces/<uuid:workspace_id>/students/", WorkspaceStudentRosterView.as_view(), name="workspace-students"),
    path("me/", MyStatsView.as_view(), name="my-stats"),
    path("events/", LogEventView.as_view(), name="log-event"),
]
