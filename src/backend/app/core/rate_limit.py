"""防滥用限流（AC-13 防爬）。

轻量实现：内存滑动窗口（单进程足够 MVP；多 worker 部署应换 Redis 计数）。
敏感端点（注册/登录/校准回传）每分钟限制。
"""

import time
from collections import defaultdict, deque

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import _error_body, CODE_BAD_REQUEST
from app.core.logging import logger

DEFAULT_RATE = 10  # 每分钟 10 次（Spec：登录/注册/支付敏感端点）
_WINDOW_SECONDS = 60


class MemoryRateLimiter:
    """进程内滑动窗口限流器。"""

    def __init__(self) -> None:
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str, limit: int = DEFAULT_RATE) -> bool:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > _WINDOW_SECONDS:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True

    def clear(self, key: str) -> None:
        self._hits.pop(key, None)


_rate_limiter = MemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """对敏感端点按 (IP + 路径) 限流。"""

    SENSITIVE_PREFIXES = ("/api/v1/auth/", "/api/v1/calibration/")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(self.SENSITIVE_PREFIXES):
            key = f"{request.client.host}:{path}"
            if not _rate_limiter.allow(key):
                logger.warning("rate limited: %s", key)
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=429,
                    content=_error_body(CODE_BAD_REQUEST, "请求过于频繁，请稍后再试"),
                )
        response: Response = await call_next(request)
        return response
