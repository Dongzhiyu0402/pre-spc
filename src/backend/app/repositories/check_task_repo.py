"""check_tasks 查询封装。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check_task import CheckTask


async def get_by_id(db: AsyncSession, task_id: int) -> CheckTask | None:
    return await db.get(CheckTask, task_id)


async def list_by_user(
    db: AsyncSession, user_id: int, page: int, limit: int
) -> tuple[list[CheckTask], int]:
    base = select(CheckTask).where(CheckTask.user_id == user_id)
    count_result = await db.execute(
        select(CheckTask.id).where(CheckTask.user_id == user_id)
    )
    total = len(count_result.scalars().all())
    result = await db.execute(
        base.order_by(CheckTask.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    return list(result.scalars().all()), total


async def create(
    db: AsyncSession,
    user_id: int,
    plan_code: str,
    file_name: str,
    file_size: int,
    word_count: int,
    engine_version: str,
) -> CheckTask:
    task = CheckTask(
        user_id=user_id,
        plan_code=plan_code,
        file_name=file_name,
        file_size=file_size,
        word_count=word_count,
        status="pending",
        engine_version=engine_version,
    )
    db.add(task)
    await db.flush()
    return task


async def update_status(db: AsyncSession, task_id: int, status: str, error_message: str | None = None) -> None:
    task = await db.get(CheckTask, task_id)
    if task is None:
        return
    task.status = status
    if error_message is not None:
        task.error_message = error_message
    await db.flush()
