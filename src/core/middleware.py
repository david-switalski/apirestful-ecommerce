import hashlib
import json
from collections.abc import Callable
from typing import Any

import jwt
import structlog
from fastapi import Request, Response, status
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.responses import Response as StarletteResponse

from src.cache.session import redis_pool

logger = structlog.get_logger()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:
        if request.method not in ["POST", "PATCH", "PUT"]:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        user_id = "anon"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = str(payload.get("sub", "anon"))
            except jwt.PyJWTError:
                logger.debug("idempotency_middleware_invalid_token")
                user_id = "anon"
            except Exception as e:
                logger.error("idempotency_middleware_token_error", error=str(e))
                user_id = "anon"

        body = await request.body()
        body_hash = hashlib.sha256(body).hexdigest()[:16]

        cache_key = f"idemp:{user_id}:{request.url.path}:{idempotency_key}:{body_hash}"

        async with Redis(connection_pool=redis_pool) as redis:
            try:
                cached_value = await redis.get(cache_key)

                if cached_value:
                    if cached_value == "PROCESSING":
                        logger.warning("idempotency_conflict_detected", key=cache_key)
                        return JSONResponse(
                            status_code=status.HTTP_409_CONFLICT,
                            content={"detail": "Request in process. Please wait."},
                        )

                    logger.info("idempotency_hit", key=cache_key)
                    data = json.loads(cached_value)
                    return JSONResponse(
                        content=data["body"],
                        status_code=data["status_code"],
                        headers=data["headers"],
                    )

                is_locked = await redis.set(cache_key, "PROCESSING", ex=60, nx=True)
                if not is_locked:
                    return JSONResponse(
                        status_code=status.HTTP_409_CONFLICT,
                        content={"detail": "Duplicate request detected."},
                    )

                async def receive() -> dict[str, Any]:
                    return {"type": "http.request", "body": body}

                request._receive = receive

                response = await call_next(request)

                if 200 <= response.status_code < 500:
                    res_body = b""
                    async for chunk in response.body_iterator:
                        res_body += chunk

                    try:
                        payload_to_cache = json.loads(res_body.decode())
                    except json.JSONDecodeError:
                        payload_to_cache = res_body.decode()
                    except Exception:
                        payload_to_cache = res_body.decode()
                    cache_data = {
                        "body": payload_to_cache,
                        "status_code": response.status_code,
                        "headers": {
                            k: v
                            for k, v in response.headers.items()
                            if k.lower() not in ["content-length", "set-cookie"]
                        },
                    }

                    await redis.set(cache_key, json.dumps(cache_data), ex=86400)

                    return StarletteResponse(
                        content=res_body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )
                else:
                    await redis.delete(cache_key)
                    return response

            except Exception as e:
                await redis.delete(cache_key)
                logger.error("idempotency_error", error=str(e))
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Idempotency layer error"},
                )
