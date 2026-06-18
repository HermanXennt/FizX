from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import AvatarUploadSerializer, PresenceUpdateSerializer, UpdateProfileSerializer, UserSerializer
from ..services import UserService


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

    @extend_schema(request=UpdateProfileSerializer, responses={200: UserSerializer})
    def patch(self, request):
        serializer = UpdateProfileSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = UserService().update_profile(user=request.user, **serializer.validated_data)
        return Response(UserSerializer(user, context={"request": request}).data)


class AvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(request=AvatarUploadSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService().upload_avatar(user=request.user, avatar_file=serializer.validated_data["avatar"])
        return Response(UserSerializer(user, context={"request": request}).data)

    @extend_schema(request=None, responses={200: UserSerializer})
    def delete(self, request):
        user = UserService().remove_avatar(user=request.user)
        return Response(UserSerializer(user, context={"request": request}).data, status=status.HTTP_200_OK)


class PresenceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PresenceUpdateSerializer, responses={200: UserSerializer})
    def patch(self, request):
        serializer = PresenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService().update_presence(user=request.user, **serializer.validated_data)
        return Response(UserSerializer(user, context={"request": request}).data)
