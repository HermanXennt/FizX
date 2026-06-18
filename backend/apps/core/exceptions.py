import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("apps.core")


class ApplicationError(APIException):
    """Base class for domain/service-layer errors raised by services.py modules.

    Service methods raise these instead of DRF's APIException subclasses so
    that the service layer has no dependency on the web framework - only
    views.py translates them into HTTP responses (which happens for free
    here since this still subclasses APIException).
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "application_error"

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail, code=code)


class NotFoundError(ApplicationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"


class PermissionDeniedError(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "permission_denied"


class ConflictError(ApplicationError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"


class ValidationError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "validation_error"


class ExternalServiceError(ApplicationError):
    """Raised when a third-party integration (LiveKit, Stripe, Google) fails."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "external_service_error"


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception in %s", context.get("view"))
        return None

    if not isinstance(response.data, dict) or "detail" not in response.data:
        envelope = {"detail": response.data}
    else:
        envelope = response.data

    error_code = getattr(exc, "default_code", None) or getattr(exc, "code", None) or "error"
    response.data = {
        "error": {
            "code": error_code,
            "message": envelope.get("detail"),
            "fields": envelope if isinstance(envelope, dict) and "detail" not in envelope else None,
        }
    }

    if response.status_code >= 500:
        logger.error("Server error: %s", exc, exc_info=True)
    elif response.status_code >= 400:
        logger.warning("Client error %s: %s", response.status_code, exc)

    return response
