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


def send_via_otp_service(*, phone_number: str, text: str) -> None:
    """Sends an arbitrary message from the shared OTP number - e.g. "a teacher
    added you to their class" pings. Distinct from the per-teacher sessions
    below: those stay read-only, this is the only thing that ever messages
    someone on the platform's behalf.
    """
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp OTP is not configured on this server.")

    try:
        response = _client().post("/api/send-message", json={"phone": phone_number, "text": text})
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp OTP service.") from exc

    if response.status_code == 404:
        raise ApplicationError(detail="This number doesn't appear to have WhatsApp.", status_code=404)
    if response.status_code == 503:
        raise ExternalServiceError(detail="WhatsApp isn't linked on the OTP service yet.")
    if response.is_error:
        raise ExternalServiceError(detail="Failed to send the WhatsApp message.")


# --- Per-teacher WhatsApp group sessions ---
#
# Separate from the OTP session above: each teacher can link their own
# personal WhatsApp account to browse and import their own group chats.
# The Node service keeps these sessions fully isolated from the OTP one and
# from each other, keyed by teacher_id (a User's id).


def start_group_session(*, teacher_id: str) -> None:
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp integration is not configured on this server.")
    try:
        response = _client().post(f"/api/teacher-sessions/{teacher_id}/start")
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp service.") from exc
    if response.is_error:
        raise ExternalServiceError(detail="Failed to start the WhatsApp session.")


def get_group_session_status(*, teacher_id: str) -> str:
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp integration is not configured on this server.")
    try:
        response = _client().get(f"/api/teacher-sessions/{teacher_id}/status")
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp service.") from exc
    if response.is_error:
        raise ExternalServiceError(detail="Failed to check the WhatsApp session status.")
    return str(response.json().get("status"))


def get_group_session_qr(*, teacher_id: str) -> str | None:
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp integration is not configured on this server.")
    try:
        response = _client().get(f"/api/teacher-sessions/{teacher_id}/qr")
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp service.") from exc
    if response.status_code == 404:
        return None
    if response.is_error:
        raise ExternalServiceError(detail="Failed to fetch the WhatsApp QR code.")
    return response.json().get("qr")


def list_whatsapp_groups(*, teacher_id: str) -> list[dict]:
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp integration is not configured on this server.")
    try:
        response = _client().get(f"/api/teacher-sessions/{teacher_id}/groups")
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp service.") from exc
    if response.status_code == 409:
        raise ApplicationError(detail="WhatsApp isn't connected yet.", status_code=409)
    if response.is_error:
        raise ExternalServiceError(detail="Failed to list WhatsApp groups.")
    return response.json().get("groups", [])


def list_group_participants(*, teacher_id: str, group_id: str) -> list[str]:
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp integration is not configured on this server.")
    try:
        response = _client().get(f"/api/teacher-sessions/{teacher_id}/groups/{group_id}/participants")
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp service.") from exc
    if response.status_code == 409:
        raise ApplicationError(detail="WhatsApp isn't connected yet.", status_code=409)
    if response.is_error:
        raise ExternalServiceError(detail="Failed to list the group's participants.")
    return response.json().get("phone_numbers", [])


def disconnect_group_session(*, teacher_id: str) -> None:
    if not settings.WHATSAPP_OTP_API_KEY:
        raise ApplicationError(detail="WhatsApp integration is not configured on this server.")
    try:
        response = _client().post(f"/api/teacher-sessions/{teacher_id}/logout")
    except httpx.HTTPError as exc:
        raise ExternalServiceError(detail="Couldn't reach the WhatsApp service.") from exc
    if response.is_error:
        raise ExternalServiceError(detail="Failed to disconnect the WhatsApp session.")
