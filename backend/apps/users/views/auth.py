from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.core.exceptions import ValidationError

from ..serializers import LogoutSerializer, RequestOtpSerializer, UserSerializer, VerifyOtpSerializer
from ..services import AuthService


def _issue_tokens_for(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RequestOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-sensitive"

    @extend_schema(request=RequestOtpSerializer, responses={200: OpenApiResponse(description="OK")})
    def post(self, request):
        serializer = RequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService().request_otp(**serializer.validated_data)
        return Response({"detail": "A verification code was sent over WhatsApp."})


class VerifyOtpView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth-sensitive"

    @extend_schema(request=VerifyOtpSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, created = AuthService().verify_otp(**serializer.validated_data)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        tokens = _issue_tokens_for(user)
        data = {"user": UserSerializer(user, context={"request": request}).data, **tokens}
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


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
