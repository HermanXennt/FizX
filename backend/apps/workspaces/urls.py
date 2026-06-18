from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import InvitationAcceptView, InvitationDeclineView, InvitationPreviewView, WorkspaceViewSet

router = DefaultRouter()
router.register("", WorkspaceViewSet, basename="workspace")

urlpatterns = [
    path("invitations/<str:token>/", InvitationPreviewView.as_view(), name="invitation-preview"),
    path("invitations/<str:token>/accept/", InvitationAcceptView.as_view(), name="invitation-accept"),
    path("invitations/<str:token>/decline/", InvitationDeclineView.as_view(), name="invitation-decline"),
    *router.urls,
]
