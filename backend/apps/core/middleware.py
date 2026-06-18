import logging
import time
import uuid

logger = logging.getLogger("apps.core")


class RequestLoggingMiddleware:
    """Logs every request with a correlation id, method, path, status and latency."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        response["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %s (%sms)",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
            extra={"request_id": request_id},
        )
        return response
