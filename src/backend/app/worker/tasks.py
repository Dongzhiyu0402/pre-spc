"""RQ 任务（查重是耗时任务，必须异步 -> AC-01）。

run_check_job 提供：
- enqueue(db, task_id, plan_params)   创建后入队（文本已落盘）
- enqueue_recheck(db, task_id, old_task_id, plan_params)  再检测入队
- _run_sync(...)                       测试/无 Redis 时的同步执行路径

worker 与 API 解耦：worker 独立进程跑 rq.Worker（见 worker.py）。
"""

import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import logger
from app.repositories import check_result_repo, check_task_repo


class _CheckJobRunner:
    """查重任务执行封装（同步引擎调用）。"""

    @staticmethod
    def _read_stored_text(task_id: int) -> str:
        path = os.path.join(settings.storage_dir, "uploads", f"{task_id}.txt")
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    @staticmethod
    def _run_engine(task_id: int, plan_params: dict, old_task_id: int | None = None) -> dict:
        from engine.pipeline import run_check

        if old_task_id is not None:
            text = _CheckJobRunner._read_stored_text(old_task_id)
        else:
            text = _CheckJobRunner._read_stored_text(task_id)
        params = dict(plan_params or {})
        params["source_label"] = "语料库"
        params["sample_count"] = 0
        result = run_check(
            text,
            params,
            index_dir=settings.resolved_engine_index_dir,
        )
        return result.as_dict()

    @staticmethod
    async def process(db: AsyncSession, task_id: int, plan_params: dict, old_task_id: int | None = None) -> None:
        """执行查重并写结果（同一事务）。"""
        await check_task_repo.update_status(db, task_id, "processing")
        await db.commit()
        try:
            engine_out = _CheckJobRunner._run_engine(task_id, plan_params, old_task_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("check job failed task=%s", task_id, exc_info=exc)
            await check_task_repo.update_status(db, task_id, "failed", str(exc))
            await db.commit()
            return

        prediction = engine_out.get("prediction", {})
        from decimal import Decimal

        raw_score = Decimal(str(engine_out.get("raw_score", 0.0)))
        est_median = Decimal(str(prediction.get("est_median", 0.0)))
        est_low = Decimal(str(prediction.get("est_low", 0.0)))
        est_high = Decimal(str(prediction.get("est_high", 0.0)))
        confidence = Decimal(str(prediction.get("confidence", 0.0)))

        # 区间一致性兜底（防沉默逻辑错误）
        if not (est_low <= est_median <= est_high):
            est_low = min(est_low, est_median)
            est_high = max(est_high, est_median)

        await check_result_repo.create(
            db,
            task_id,
            raw_score,
            est_median,
            est_low,
            est_high,
            confidence,
            engine_out.get("segments", []),
        )
        await check_task_repo.update_status(db, task_id, "succeeded")
        await db.commit()


class _CheckJobQueue:
    """任务队列封装：RQ 优先，无 Redis / 测试时同步执行。"""

    @staticmethod
    def _sync_mode() -> bool:
        return os.environ.get("PRE_RQ_SYNC", "0") == "1" or settings.debug

    async def enqueue(self, db: AsyncSession, task_id: int, plan_params: dict) -> None:
        if self._sync_mode():
            await _CheckJobRunner.process(db, task_id, plan_params)
            return
        self._enqueue_rq("process_check", task_id, plan_params)

    async def enqueue_recheck(self, db: AsyncSession, task_id: int, old_task_id: int, plan_params: dict) -> None:
        if self._sync_mode():
            await _CheckJobRunner.process(db, task_id, plan_params, old_task_id)
            return
        self._enqueue_rq("recheck_check", task_id, old_task_id, plan_params)

    @staticmethod
    def _enqueue_rq(job_name: str, *args) -> None:  # pragma: no cover
        import redis
        from rq import Queue

        conn = redis.from_url(settings.redis_url)
        queue = Queue(settings.rq_queue_name, connection=conn)
        if job_name == "process_check":
            queue.enqueue(process_check, args[0], args[1])
        else:
            queue.enqueue(recheck_check, args[0], args[1], args[2])


run_check_job = _CheckJobQueue()


def process_check(task_id: int, plan_params: dict) -> None:  # pragma: no cover
    """RQ worker 入口：process_check。"""
    asyncio.run(_run_worker_job(task_id, plan_params))


def recheck_check(task_id: int, old_task_id: int, plan_params: dict) -> None:  # pragma: no cover
    """RQ worker 入口：recheck_check。"""
    asyncio.run(_run_worker_job(task_id, plan_params, old_task_id))


async def _run_worker_job(task_id: int, plan_params: dict, old_task_id: int | None = None) -> None:  # pragma: no cover
    from app.database import SessionLocal

    async with SessionLocal() as db:
        await _CheckJobRunner.process(db, task_id, plan_params, old_task_id)
