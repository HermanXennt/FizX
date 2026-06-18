from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardResultsPagination

from .repositories import NotificationRepository
from .serializers import NotificationSerializer
from .services import NotificationService


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: NotificationSerializer(many=True)})
    def get(self, request):
        unread_only = request.query_params.get("unread") == "true"
        queryset = NotificationRepository().for_user(request.user, unread_only=unread_only)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(NotificationSerializer(page, many=True).data)


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: None})
    def get(self, request):
        return Response({"count": NotificationRepository().unread_count(request.user)})


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: NotificationSerializer})
    def post(self, request, notification_id):
        notification = NotificationService().mark_read(notification_id=notification_id, user=request.user)
        return Response(NotificationSerializer(notification).data)


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={200: None})
    def post(self, request):
        count = NotificationService().mark_all_read(user=request.user)
        return Response({"marked_read": count})
