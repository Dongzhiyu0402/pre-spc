"""用量端点：GET /users/me/usage（AC-13 余额实时可见）。"""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbDep
from app.schemas import ok
from app.schemas.report import UsageOut

router = APIRouter(prefix="/api/v1/users/me", tags=["usage"])


@router.get("/usage")
async def get_usage(db: DbDep, user: CurrentUser) -> dict:
    # 直接从当前用户快照读取（创建任务时已实时扣减并 commit）
    return ok(UsageOut(free_quota=user.free_quota, points=user.points).model_dump(mode="json"))
