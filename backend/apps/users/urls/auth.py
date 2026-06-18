from django.urls import path

from ..views.auth import FizXTokenRefreshView, LogoutView, RequestOtpView, VerifyOtpView

app_name = "auth"

urlpatterns = [
    path("otp/request/", RequestOtpView.as_view(), name="otp-request"),
    path("otp/verify/", VerifyOtpView.as_view(), name="otp-verify"),
    path("refresh/", FizXTokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
