import httpx
from django.conf import settings

from apps.core.exceptions import ApplicationError, ExternalServiceError

REQUEST_TIMEOUT_SECONDS = 15


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=settings.WHATSAPP_OTP_URL,
        headers={"X-API-Key": settings.WHATSAPP_OTP_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def send_otp(*, phone_number: str) -> None:
    """Asks the whatsapp-otp service to generate and deliver a one-time code.

    That service owns the OTP's lifecycle entirely (generation, storage,
    expiry, delivery) - this app never sees the code itself, only whether
    the request to send it succeeded.
    """
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp OTP is not configured on this server.")

    try:
        response = _client().post("/api/send-otp", json={"phone": phone_number})
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp OTP service.") from exc

    if response.status_code == 404:
        raise ApplicationError(detail="This number doesn't appear to have WhatsApp.", status_code=404)
    if response.status_code == 503:
        raise ExternalServiceError(detail="WhatsApp isn't linked on the OTP service yet.")
    if response.is_error:
        raise ExternalServiceError(detail="Failed to send the WhatsApp verification code.")


def verify_otp(*, phone_number: str, code: str) -> bool:
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp OTP is not configured on this server.")

    try:
        response = _client().post("/api/verify-otp", json={"phone": phone_number, "code": code})
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp OTP service.") from exc

    if response.is_error:
        raise ExternalServiceError(detail="Failed to verify the WhatsApp code.")

    return bool(response.json().get("valid"))
