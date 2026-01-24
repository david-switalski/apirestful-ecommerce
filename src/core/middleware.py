import json
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import Request, Response
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.cache.session import redis_pool

logger = structlog.get_logger()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        if request.method not in ["POST", "PATCH"]:
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return await call_next(request)

        cache_key = f"idempotency:{key}"

        async with Redis(connection_pool=redis_pool) as redis:
            if cached := await redis.get(cache_key):
                logger.info("idempotency_hit", key=key)
                data = json.loads(cached)
                return JSONResponse(
                    content=data["body"],
                    status_code=data["status_code"],
                    headers=data["headers"],
                )

            response = await call_next(request)

            if 200 <= response.status_code < 300:
                body_bytes = [section async for section in response.body_iterator]
                response.body_iterator = iter(body_bytes)
                body_content = b"".join(body_bytes).decode()

                cache_data = {
                    "body": json.loads(body_content),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }
                await redis.set(cache_key, json.dumps(cache_data), ex=86400)
                logger.info("idempotency_saved", key=key)

            return response
