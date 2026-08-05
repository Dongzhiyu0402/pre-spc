"""额度/积分扣减与流水（原子事务，AC-13 优先扣积分且余额实时可见）。"""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import payment_required
from app.models.user import User
from app.repositories import point_repo


async def consume_for_check(db: AsyncSession, user: User, cost_points: int = 1) -> User:
    """查重扣费：优先扣积分，不足则扣免费次数。失败抛 402。

    返回更新后的 user（已 flush，未 commit）。
    """
    if user.points >= cost_points:
        user.points -= cost_points
        await point_repo.create_transaction(db, user.id, -cost_points, "consume", "查重消耗积分")
    elif user.free_quota > 0:
        user.free_quota -= 1
        # 免费次数非积分变动，point_transactions.amount <> 0，故不记流水
    else:
        raise payment_required("免费次数已用完，请充值积分后再试")
    await db.flush()
    return user


async def reward_calibration(db: AsyncSession, user: User, reward_points: int = 2) -> User:
    """校准回传奖励积分（"回传报告换免费次数"激励，Spec §11）。"""
    user.points += reward_points
    await point_repo.create_transaction(db, user.id, reward_points, "calibration_reward", "回传真实查重报告奖励")
    await db.flush()
    return user
