from django.db.models import Q, QuerySet

from apps.core.repositories import BaseRepository

from .models import User


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_phone_number(self, phone_number: str) -> User | None:
        return self.get_queryset().filter(phone_number=phone_number).first()

    def phone_number_exists(self, phone_number: str) -> bool:
        return self.get_queryset().filter(phone_number=phone_number).exists()

    def search_contacts(self, *, requester: User, query: str) -> QuerySet[User]:
        """Users the requester shares a workspace with (as teacher or
        student, in either direction), matching the query against name or
        phone number - scopes "invite a contact" to people already known to
        the platform through a class, rather than exposing every registered
        phone number to a free-text search."""
        workspace_ids = requester.workspace_memberships.values_list("workspace_id", flat=True)
        return (
            self.get_queryset()
            .filter(workspace_memberships__workspace_id__in=workspace_ids)
            .filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(phone_number__icontains=query)
            )
            .exclude(id=requester.id)
            .distinct()[:20]
        )
