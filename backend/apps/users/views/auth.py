from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.core.exceptions import ValidationError

from ..serializers import (
    EmailVerificationConfirmSerializer,
    FizXTokenObtainPairSerializer,
    GoogleLoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from ..services import AuthService


def _issue_tokens_for(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService().register(**serializer.validated_data)
        tokens = _issue_tokens_for(user)
        data = {"user": UserSerializer(user, context={"request": request}).data, **tokens}
        return Response(data, status=status.HTTP_201_CREATED)


class FizXTokenObtainPairView(TokenObtainPairView):
    serializer_class = FizXTokenObtainPairSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            email = request.data.get(FizXTokenObtainPairSerializer.username_field)
            from ..models import User

            User.objects.filter(email__iexact=email).update(last_login=timezone.now())
        return response


class FizXTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError as exc:
            raise ValidationError(detail="Invalid or already-expired refresh token.") from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-sensitive"

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: OpenApiResponse(description="OK")})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService().request_password_reset(**serializer.validated_data)
        return Response(
            {"detail": "If an account with that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-sensitive"

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: OpenApiResponse(description="OK")})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService().confirm_password_reset(**serializer.validated_data)
        return Response({"detail": "Your password has been reset successfully."})


class ResendVerificationEmailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "auth-sensitive"

    @extend_schema(request=None, responses={200: OpenApiResponse(description="OK")})
    def post(self, request):
        AuthService().send_verification_email(request.user)
        return Response({"detail": "Verification email sent."})


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-sensitive"

    @extend_schema(request=EmailVerificationConfirmSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService().confirm_email_verification(**serializer.validated_data)
        return Response(UserSerializer(user, context={"request": request}).data)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(request=GoogleLoginSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService().login_with_google(id_token_str=serializer.validated_data["id_token"])
        tokens = _issue_tokens_for(user)
        data = {"user": UserSerializer(user, context={"request": request}).data, **tokens}
        return Response(data, status=status.HTTP_200_OK)
