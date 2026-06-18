from django.urls import path

from .views import (
    LiveKitEgressWebhookView,
    MeetingRecordingsView,
    MyRecordingsView,
    RecordingDetailView,
    StopRecordingView,
)

app_name = "recordings"

urlpatterns = [
    path("", MyRecordingsView.as_view(), name="my-recordings"),
    path("meetings/<uuid:meeting_id>/", MeetingRecordingsView.as_view(), name="meeting-recordings"),
    path("<uuid:recording_id>/", RecordingDetailView.as_view(), name="detail"),
    path("<uuid:recording_id>/stop/", StopRecordingView.as_view(), name="stop"),
    path("webhook/", LiveKitEgressWebhookView.as_view(), name="webhook"),
]
