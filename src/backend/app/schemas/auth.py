"""认证请求/响应模型（与 openapi.yaml auth 对齐）。"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72, description="至少 8 位")
    nickname: str = Field(min_length=1, max_length=30)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: str
    nickname: str
    role: str
    free_quota: int
    points: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthData(BaseModel):
    user: UserOut
    tokens: TokensOut
