"""方案列表业务（DB 配置驱动，AC-11 新增平台无需发版）。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import plan_repo
from app.schemas.check import PlanOut


async def list_plans(db: AsyncSession) -> list[PlanOut]:
    plans = await plan_repo.list_enabled(db)
    out: list[PlanOut] = []
    for p in plans:
        params = p.params_json or {}
        price_info = params.get("price_info", {})
        out.append(
            PlanOut(
                code=p.code,
                name=p.name,
                type=p.type,
                price_info=price_info,
                enabled=p.enabled,
            )
        )
    return out
