"""统一响应信封 {code, data, message} 与错误模型。"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = "ok"


class ErrorDetail(BaseModel):
    loc: list[str] = Field(default_factory=list)
    msg: str = ""
    type: str = ""


class ErrorResponse(BaseModel):
    code: int
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "data": data, "message": message}
