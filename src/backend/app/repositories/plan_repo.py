"""plans 查询封装。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan


async def list_enabled(db: AsyncSession) -> list[Plan]:
    result = await db.execute(select(Plan).where(Plan.enabled.is_(True)).order_by(Plan.id))
    return list(result.scalars().all())


async def get_by_code(db: AsyncSession, code: str) -> Plan | None:
    result = await db.execute(select(Plan).where(Plan.code == code))
    return result.scalar_one_or_none()


async def seed_defaults(db: AsyncSession) -> None:
    """种子方案（幂等，按 code 判重）。"""
    defaults = [
        {"code": "cnki_sim", "name": "知网模拟", "type": "engine", "params_json": {"platform": "cnki", "paper_type": "undergrad", "price_info": {"cost_points": 1}}},
        {"code": "vip_sim", "name": "维普模拟", "type": "engine", "params_json": {"platform": "vip", "paper_type": "undergrad", "price_info": {"cost_points": 1}}},
        {"code": "wanfang_sim", "name": "万方模拟", "type": "engine", "params_json": {"platform": "wanfang", "paper_type": "undergrad", "price_info": {"cost_points": 1}}},
        {"code": "api_placeholder", "name": "API 平台（预留）", "type": "api", "params_json": {"price_info": {"cost_points": 5}}},
    ]
    existing = await list_enabled(db)
    existing_codes = {p.code for p in existing}
    for item in defaults:
        if item["code"] in existing_codes:
            continue
        db.add(Plan(**item))
    await db.flush()
