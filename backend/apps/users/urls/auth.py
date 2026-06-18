from django.urls import path

from ..views.auth import (
    FizXTokenObtainPairView,
    FizXTokenRefreshView,
    GoogleLoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    ResendVerificationEmailView,
    VerifyEmailView,
)

app_name = "auth"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", FizXTokenObtainPairView.as_view(), name="login"),
    path("refresh/", FizXTokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("email/verify/resend/", ResendVerificationEmailView.as_view(), name="email-verify-resend"),
    path("email/verify/confirm/", VerifyEmailView.as_view(), name="email-verify-confirm"),
]
