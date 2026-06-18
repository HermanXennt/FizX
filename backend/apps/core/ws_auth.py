from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user_from_token(raw_token: str):
    from apps.users.models import User

    try:
        validated_token = AccessToken(raw_token)
        user_id = validated_token["user_id"]
        return User.objects.get(id=user_id, is_active=True)
    except (TokenError, InvalidToken, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Authenticates WebSocket connections using `?token=<access_token>`.

    Browsers cannot set Authorization headers on WebSocket handshakes, so
    the JWT access token travels as a query parameter instead. This runs
    once per connection, before any consumer code, and populates
    `scope["user"]` exactly like DRF's JWTAuthentication does for HTTP.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        scope["user"] = await _get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
