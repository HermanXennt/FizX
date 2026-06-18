from __future__ import annotations

from typing import Any, Generic, TypeVar

from django.db.models import Model, QuerySet

ModelT = TypeVar("ModelT", bound=Model)


class BaseRepository(Generic[ModelT]):
    """Thin data-access layer over a single Django model.

    Services depend on repositories rather than the ORM directly, so
    persistence concerns (querysets, select_related/prefetch_related,
    locking) live in one place per model and can be swapped or mocked in
    tests without touching business logic in services.py.
    """

    model: type[ModelT]

    def get_queryset(self) -> QuerySet[ModelT]:
        return self.model.objects.all()

    def get_by_id(self, pk: Any) -> ModelT | None:
        return self.get_queryset().filter(pk=pk).first()

    def get_by_id_or_raise(self, pk: Any) -> ModelT:
        from apps.core.exceptions import NotFoundError

        instance = self.get_by_id(pk)
        if instance is None:
            raise NotFoundError(detail=f"{self.model.__name__} not found.")
        return instance

    def list(self, **filters: Any) -> QuerySet[ModelT]:
        return self.get_queryset().filter(**filters)

    def create(self, **fields: Any) -> ModelT:
        instance = self.model(**fields)
        instance.full_clean()
        instance.save()
        return instance

    def update(self, instance: ModelT, **fields: Any) -> ModelT:
        for key, value in fields.items():
            setattr(instance, key, value)
        instance.full_clean()
        instance.save(update_fields=list(fields.keys()) + ["updated_at"] if hasattr(instance, "updated_at") else list(fields.keys()))
        return instance

    def delete(self, instance: ModelT) -> None:
        instance.delete()
