"""认证端点：register/login/refresh/me。"""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbDep, RefreshToken
from app.schemas import ok
from app.schemas.auth import AuthData, LoginRequest, RefreshRequest, RegisterRequest, TokensOut, UserOut
from app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(db: DbDep, body: RegisterRequest) -> dict:
    user, tokens = await auth_service.register(db, body.email, body.password, body.nickname)
    return ok(AuthData(user=user, tokens=tokens).model_dump(mode="json"))


@router.post("/login")
async def login(db: DbDep, body: LoginRequest) -> dict:
    user, tokens = await auth_service.login(db, body.email, body.password)
    return ok(AuthData(user=user, tokens=tokens).model_dump(mode="json"))


@router.post("/refresh")
async def refresh(db: DbDep, body: RefreshRequest) -> dict:
    tokens = await auth_service.refresh(db, body.refresh_token)
    return ok(TokensOut.model_validate(tokens).model_dump(mode="json"))


@router.get("/me")
async def me(db: DbDep, user: CurrentUser) -> dict:
    out = await auth_service.get_me(db, user.id)
    return ok(UserOut.model_validate(out).model_dump(mode="json"))
