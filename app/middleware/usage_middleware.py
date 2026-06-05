from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from app.api.deps import get_db
from app.services.usage_limiter import UsageLimiterService


class UsageMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        if request.url.path.startswith("/auth") \
        or request.url.path.startswith("/docs") \
        or request.url.path.startswith("/openapi") \
        or request.url.path.startswith("/health"):
            return await call_next(request)

        user = getattr(request.state, "user", None)

        if not user:
            return await call_next(request)

        async for db in get_db():

            await UsageLimiterService.check_and_increment(
                db,
                user.id
            )

            response = await call_next(request)

            return response