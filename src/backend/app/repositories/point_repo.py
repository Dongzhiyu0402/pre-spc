"""积分/次数流水查询封装。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point_transaction import PointTransaction


async def create_transaction(
    db: AsyncSession, user_id: int, amount: int, type: str, reason: str = ""
) -> PointTransaction:
    tx = PointTransaction(user_id=user_id, amount=amount, type=type, reason=reason)
    db.add(tx)
    await db.flush()
    return tx


async def list_by_user(db: AsyncSession, user_id: int, limit: int = 50) -> list[PointTransaction]:
    result = await db.execute(
        select(PointTransaction)
        .where(PointTransaction.user_id == user_id)
        .order_by(PointTransaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
