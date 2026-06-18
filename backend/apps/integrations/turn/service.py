import base64
import hashlib
import hmac
import time

from django.conf import settings

from apps.core.exceptions import ApplicationError

CREDENTIAL_TTL_SECONDS = 24 * 60 * 60


def generate_turn_credentials(*, user_identifier: str, turn_host: str) -> dict:
    """Generates time-limited TURN credentials using coturn's REST API
    long-term credential mechanism: username is `"<expiry-unix-ts>:<user>"`,
    and the password is `base64(HMAC-SHA1(shared_secret, username))`. coturn
    validates the same way using its own `--static-auth-secret`, so neither
    side ever needs to store or look up individual credentials.
    """
    if not settings.TURN_SHARED_SECRET:
        raise ApplicationError(detail="TURN is not configured on this server.")

    expiry = int(time.time()) + CREDENTIAL_TTL_SECONDS
    username = f"{expiry}:{user_identifier}"
    digest = hmac.new(settings.TURN_SHARED_SECRET.encode(), username.encode(), hashlib.sha1).digest()
    credential = base64.b64encode(digest).decode()

    return {
        "username": username,
        "credential": credential,
        "ttl": CREDENTIAL_TTL_SECONDS,
        "urls": [
            f"turn:{turn_host}:3478?transport=udp",
            f"turn:{turn_host}:3478?transport=tcp",
        ],
    }
