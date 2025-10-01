from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer  # type: ignore[import-untyped]

from arkad.jwt_utils import jwt_decode
from user_models.models import User


class AuthenticatedAsyncWebsocketConsumer(AsyncWebsocketConsumer):  # type: ignore[misc]
    """
    Base consumer providing typed helpers for query parsing and authentication.
    Prefers session/cookie auth via scope['user'] when available; otherwise falls back
    to `token` query param with JWT validation.
    Subclasses should call `await self.authenticate_from_query()` inside connect.
    """

    user: User  # set after authentication
    query_params: Dict[str, List[str]]

    def parse_query_params(self) -> Dict[str, List[str]]:
        query_string: str = self.scope.get("query_string", b"").decode()
        self.query_params = parse_qs(query_string)
        return self.query_params

    def get_query_param(
        self, name: str, default: Optional[str] = None
    ) -> Optional[str]:
        params = getattr(self, "query_params", None) or self.parse_query_params()
        values = params.get(name)
        if not values:
            return default
        return values[0]

    async def authenticate_from_query(
        self, *, expected_token_type: Optional[str] = "websocket"
    ) -> bool:
        """Authenticate connection and set `self.user`.
        Order of precedence:
        1) If scope['user'] is present and authenticated (via Django session/cookies), use it.
        2) Otherwise, authenticate using `token` query param (JWT). If `expected_token_type` is not None,
           it must match the decoded token's `token_type`.
        Returns True on success; on failure, closes the connection with code 4001 and returns False.
        """
        # Prefer cookie-based session auth if available
        scope_user = self.scope.get("user")
        if scope_user is not None and getattr(scope_user, "is_authenticated", False):
            self.user = scope_user
            return True

        # Fallback to explicit token in query string
        token: Optional[str] = self.get_query_param("token")
        if not token:
            await self.close(code=4001)
            return False

        try:
            decoded: Dict[str, Any] = jwt_decode(token)
            if (
                expected_token_type is not None
                and decoded.get("token_type") != expected_token_type
            ):
                await self.close(code=4001)
                return False

            user_id_raw: Any = decoded.get("user_id")
            if user_id_raw is None:
                await self.close(code=4001)
                return False

            user_id: int = int(user_id_raw)
            # Minimal sync DB call; subclasses may override to fetch related data.
            user: Optional[User] = await self._get_user(user_id)
            if user is None or not user.is_active:
                await self.close(code=4001)
                return False

            self.user = user
            return True
        except Exception:
            await self.close(code=4001)
            return False

    async def _get_user(self, user_id: int) -> Optional[User]:
        # Import locally to avoid global decorator type confusion and keep strict typing.
        from channels.db import database_sync_to_async  # type: ignore[import-untyped]

        def _sync() -> Optional[User]:
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                return None

        return await database_sync_to_async(_sync)()  # type: ignore[no-any-return]
