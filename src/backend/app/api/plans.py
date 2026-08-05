"""方案端点：GET /plans（AC-11 DB 配置驱动）。"""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbDep
from app.schemas import ok
from app.services import plan_service

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])


@router.get("")
async def list_plans(db: DbDep, user: CurrentUser) -> dict:
    plans = await plan_service.list_plans(db)
    return ok([p.model_dump(mode="json") for p in plans])
