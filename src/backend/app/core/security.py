"""JWT 签发/校验 + 密码哈希（bcrypt）。

- access token 15min，refresh token 7d（Spec §4）
- 密码 bcrypt 哈希，绝不明文存储
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class TokenError(Exception):
    """token 无效或过期。"""


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, TOKEN_TYPE_ACCESS, timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, TOKEN_TYPE_REFRESH, timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str, expected_type: str) -> int:
    """解码并校验 token，返回 user_id。失败抛 TokenError。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError("token 无效或已过期") from exc
    if payload.get("type") != expected_type:
        raise TokenError("token 类型不匹配")
    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise TokenError("token 载荷无效") from exc


def access_token_expires_in() -> int:
    return settings.access_token_expire_minutes * 60
