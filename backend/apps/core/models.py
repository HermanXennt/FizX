import uuid

from django.db import models


class BaseModel(models.Model):
    """Abstract base providing a UUID primary key and timestamps.

    UUID primary keys are used project-wide (instead of auto-incrementing
    integers) so that meeting room names, invitation links, and other
    identifiers exposed in URLs are not sequentially guessable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
