"""API 依赖注入：get_db / get_current_user / get_current_refresh_token。"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.exceptions import unauthorized
from app.database import get_db
from app.models.user import User
from app.repositories import user_repo

_bearer = HTTPBearer(auto_error=False)

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """解析 access token -> 当前用户。"""
    if credentials is None:
        raise unauthorized()
    try:
        user_id = security.decode_token(credentials.credentials, security.TOKEN_TYPE_ACCESS)
    except security.TokenError as exc:
        raise unauthorized(str(exc)) from exc
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise unauthorized("用户不存在")
    return user


async def get_refresh_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str:
    """解析 refresh token（用于 /auth/refresh 响应体，但校验在 service 完成）。"""
    if credentials is None:
        raise unauthorized()
    return credentials.credentials


CurrentUser = Annotated[User, Depends(get_current_user)]
RefreshToken = Annotated[str, Depends(get_refresh_token)]
