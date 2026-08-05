"""认证业务：注册/登录/刷新/当前用户（AC-12 注册送次数）。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import security
from app.core.exceptions import bad_request, conflict, unauthorized
from app.models.user import User
from app.repositories import user_repo
from app.schemas.auth import TokensOut, UserOut


def _tokens_for(user_id: int) -> TokensOut:
    return TokensOut(
        access_token=security.create_access_token(user_id),
        refresh_token=security.create_refresh_token(user_id),
        token_type="bearer",
        expires_in=security.access_token_expires_in(),
    )


async def register(db: AsyncSession, email: str, password: str, nickname: str) -> tuple[UserOut, TokensOut]:
    email = email.strip().lower()
    existing = await user_repo.get_by_email(db, email)
    if existing:
        raise conflict("该邮箱已注册")
    password_hash = security.hash_password(password)
    user = await user_repo.create(db, email, password_hash, nickname, settings.register_free_quota)
    await db.commit()
    return UserOut.model_validate(user), _tokens_for(user.id)


async def login(db: AsyncSession, email: str, password: str) -> tuple[UserOut, TokensOut]:
    user = await user_repo.get_by_email(db, email.strip().lower())
    if not user or not security.verify_password(password, user.password_hash):
        raise unauthorized("邮箱或密码错误")
    return UserOut.model_validate(user), _tokens_for(user.id)


async def refresh(db: AsyncSession, refresh_token: str) -> TokensOut:
    try:
        user_id = security.decode_token(refresh_token, security.TOKEN_TYPE_REFRESH)
    except security.TokenError as exc:
        raise unauthorized(str(exc)) from exc
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise unauthorized("用户不存在")
    return _tokens_for(user.id)


async def get_me(db: AsyncSession, user_id: int) -> UserOut:
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise bad_request("用户不存在")
    return UserOut.model_validate(user)
