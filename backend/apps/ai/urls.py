from django.urls import path

from .views import AskAiView

app_name = "ai"

urlpatterns = [
    path("ask/", AskAiView.as_view(), name="ask"),
]
