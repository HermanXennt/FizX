from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1_patterns = [
    path("auth/", include("apps.users.urls.auth")),
    path("users/", include("apps.users.urls.users")),
    path("workspaces/", include("apps.workspaces.urls")),
    path("meetings/", include("apps.meetings.urls")),
    path("chat/", include("apps.chat.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("recordings/", include("apps.recordings.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("payments/", include("apps.payments.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
