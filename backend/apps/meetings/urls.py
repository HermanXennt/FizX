from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import IceServersView, MeetingViewSet

router = DefaultRouter()
router.register("", MeetingViewSet, basename="meeting")

urlpatterns = [
    path("ice-servers/", IceServersView.as_view(), name="ice-servers"),
    *router.urls,
]
