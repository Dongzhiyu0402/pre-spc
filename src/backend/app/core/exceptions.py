"""统一异常与错误码 -> 响应信封 {code, data, message}。"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# 业务错误码（code 非 0，映射 HTTP 状态）
CODE_BAD_REQUEST = 40000
CODE_UNAUTHORIZED = 40100
CODE_PAYMENT_REQUIRED = 40200  # 次数/积分不足
CODE_FORBIDDEN = 40300
CODE_NOT_FOUND = 40400
CODE_CONFLICT = 40900
CODE_VALIDATION = 42200
CODE_INTERNAL = 50000


class ApiError(Exception):
    """业务异常。"""

    def __init__(self, status_code: int, code: int, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def bad_request(message: str) -> ApiError:
    return ApiError(400, CODE_BAD_REQUEST, message)


def unauthorized(message: str = "未认证或登录已过期") -> ApiError:
    return ApiError(401, CODE_UNAUTHORIZED, message)


def payment_required(message: str) -> ApiError:
    return ApiError(402, CODE_PAYMENT_REQUIRED, message)


def forbidden(message: str) -> ApiError:
    return ApiError(403, CODE_FORBIDDEN, message)


def not_found(message: str = "资源不存在") -> ApiError:
    return ApiError(404, CODE_NOT_FOUND, message)


def conflict(message: str) -> ApiError:
    return ApiError(409, CODE_CONFLICT, message)


def _error_body(code: int, message: str, errors: list | None = None) -> dict:
    body: dict = {"code": code, "message": message}
    if errors:
        body["errors"] = errors
    return body


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = CODE_NOT_FOUND if exc.status_code == 404 else exc.status_code * 100
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": [str(x) for x in err.get("loc", [])], "msg": err.get("msg", ""), "type": err.get("type", "")}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body(CODE_VALIDATION, "请求参数校验失败", errors),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
        from app.core.logging import logger

        logger.exception("unhandled error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_error_body(CODE_INTERNAL, "Internal server error"),
        )
