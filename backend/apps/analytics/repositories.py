from apps.core.repositories import BaseRepository

from .models import AnalyticsEvent


class AnalyticsEventRepository(BaseRepository[AnalyticsEvent]):
    model = AnalyticsEvent
