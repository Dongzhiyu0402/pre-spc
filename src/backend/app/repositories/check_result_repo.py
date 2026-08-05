"""check_results 查询封装。"""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check_result import CheckResult


async def get_by_task_id(db: AsyncSession, task_id: int) -> CheckResult | None:
    from sqlalchemy import select

    result = await db.execute(select(CheckResult).where(CheckResult.task_id == task_id))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    task_id: int,
    raw_score: Decimal,
    est_median: Decimal,
    est_low: Decimal,
    est_high: Decimal,
    confidence: Decimal,
    segments_json: list,
) -> CheckResult:
    result = CheckResult(
        task_id=task_id,
        raw_score=raw_score,
        est_median=est_median,
        est_low=est_low,
        est_high=est_high,
        confidence=confidence,
        segments_json=segments_json,
    )
    db.add(result)
    await db.flush()
    return result
