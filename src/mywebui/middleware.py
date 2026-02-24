"""Authentication middleware."""

from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from mywebui.core import auth as auth_service
from mywebui.core import users as users_service
from mywebui.db import connection


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to authenticate users from session cookie."""

    EXCLUDED_PATHS = {
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and authenticate the user."""
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        if request.url.path.startswith("/api/v1/auth") and request.url.path not in ["/api/v1/auth/login", "/api/v1/auth/register"]:
            pass
        elif not request.url.path.startswith("/api/"):
            return await call_next(request)

        token = request.cookies.get("session_token")

        if not token:
            if request.url.path.startswith("/api/v1/") and request.url.path not in ["/api/v1/auth/login", "/api/v1/auth/register"]:
                return Response(
                    content='{"detail": "Not authenticated"}',
                    status_code=401,
                    media_type="application/json",
                )
            return await call_next(request)

        docs_db = connection.get_docs_session_factory()
        async with docs_db() as db:
            users_result = await db.execute(
                "SELECT username FROM sqlite_master WHERE type='table' AND name='users'"
            )
            table_exists = users_result.fetchone() is not None

            if not table_exists:
                return await call_next(request)

        for username in connection._user_engines.keys():
            user_db = connection.get_user_session_factory(username)
            async with user_db() as db:
                session = await auth_service.get_session_by_token(db, token)

                if session:
                    if session.expires_at < datetime.utcnow():
                        return Response(
                            content='{"detail": "Session expired"}',
                            status_code=401,
                            media_type="application/json",
                        )

                    user_result = await connection.get_docs_session_factory()
                    async with user_result() as udb:
                        user = await users_service.get_user_by_id(udb, session.user_id)

                        if user and user.is_active:
                            request.state.user_id = user.id
                            request.state.username = user.username
                            request.state.role = user.role

                            await auth_service.refresh_session(db, session)
                            break

        return await call_next(request)
