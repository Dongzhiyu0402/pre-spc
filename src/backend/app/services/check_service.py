"""查重任务业务：创建/状态/历史/再检测（AC-01/03/04/13）。"""

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import bad_request, not_found
from app.models.user import User
from app.repositories import check_task_repo, plan_repo
from app.schemas.check import CheckTaskDetail, CheckTaskSummary, CheckResultSummary
from app.services import quota_service
from app.worker.tasks import run_check_job

ALLOWED_EXT = {".txt", ".md", ".docx", ".pdf"}
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # ≤50MB


class _ParsedFile:
    """上传文件解析结果。"""

    def __init__(self, file_name: str, file_size: int, text: str, word_count: int) -> None:
        self.file_name = file_name
        self.file_size = file_size
        self.text = text
        self.word_count = word_count


def _ext(file_name: str) -> str:
    return Path(file_name).suffix.lower()


def _validate_and_extract(file_name: str, file_size: int, content: bytes) -> _ParsedFile:
    """校验文件类型/大小并抽取文本（AC-02/03）。

    超限或空文件必须抛错且不消耗次数（AC-03）。
    """
    if file_size > _MAX_UPLOAD_BYTES:
        raise bad_request("文件超过 50MB 限制")
    ext = _ext(file_name)
    if ext not in ALLOWED_EXT:
        raise bad_request(f"不支持的文件类型: {ext or '未知'}，仅支持 txt/md/docx/pdf")

    from engine.cleaning.doc_extractor import extract_text_from_bytes

    try:
        raw_text = extract_text_from_bytes(content, file_name)
    except Exception as exc:
        raise bad_request(f"文档解析失败: {exc}") from exc

    # 字数统计（清洗后中文字符数）
    from engine.cleaning.text_cleaner import clean_text

    cleaned = clean_text(raw_text)
    word_count = sum(1 for ch in cleaned if "\u4e00" <= ch <= "\u9fff")
    if word_count == 0:
        raise bad_request("文件内容为空，无法查重")
    if word_count > settings.max_word_count:
        raise bad_request(f"文件超过 {settings.max_word_count} 字上限")
    return _ParsedFile(file_name=file_name, file_size=file_size, text=raw_text, word_count=word_count)


def _persist_text(task_id: int, text: str) -> str:
    """把抽取的原文落盘（本地卷；生产加密+30 天清理）。"""
    upload_dir = os.path.join(settings.storage_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, f"{task_id}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


async def create_check(
    db: AsyncSession,
    user: User,
    file_name: str,
    file_size: int,
    content: bytes,
    plan_code: str,
) -> CheckTaskSummary:
    """创建查重任务：校验 -> 扣费 -> 建任务 -> 落盘 -> 入队。"""
    plan = await plan_repo.get_by_code(db, plan_code)
    if not plan or not plan.enabled:
        raise bad_request(f"方案不存在或未启用: {plan_code}")

    parsed = _validate_and_extract(file_name, file_size, content)
    await quota_service.consume_for_check(db, user, cost_points=1)
    from engine import __version__ as engine_version

    task = await check_task_repo.create(
        db,
        user.id,
        plan_code,
        parsed.file_name,
        parsed.file_size,
        parsed.word_count,
        engine_version,
    )
    _persist_text(task.id, parsed.text)
    await db.commit()

    # 异步入队（RQ）；测试/调试模式同步执行
    await run_check_job.enqueue(db, task.id, plan.params_json or {})
    return _summary_of(task)


async def get_check_detail(db: AsyncSession, user_id: int, task_id: int) -> CheckTaskDetail:
    task = await check_task_repo.get_by_id(db, task_id)
    if not task or task.user_id != user_id:
        raise not_found("任务不存在或无权访问")
    detail = CheckTaskDetail(**_summary_of(task).model_dump())
    if task.status == "failed":
        detail.error = task.error_message or "查重失败"
    if task.status == "succeeded":
        from app.repositories import check_result_repo

        result = await check_result_repo.get_by_task_id(db, task.id)
        if result:
            detail.result = CheckResultSummary(
                est_median=float(result.est_median),
                est_low=float(result.est_low),
                est_high=float(result.est_high),
                confidence=float(result.confidence),
            )
    return detail


async def list_checks(db: AsyncSession, user_id: int, page: int, limit: int) -> tuple[list[CheckTaskSummary], int]:
    tasks, total = await check_task_repo.list_by_user(db, user_id, page, limit)
    return [_summary_of(t) for t in tasks], total


async def recheck(db: AsyncSession, user: User, task_id: int, plan_code: str) -> CheckTaskSummary:
    """再次检测：以原文档重建任务（换方案）。"""
    old_task = await check_task_repo.get_by_id(db, task_id)
    if not old_task or old_task.user_id != user.id:
        raise not_found("任务不存在或无权访问")
    plan = await plan_repo.get_by_code(db, plan_code)
    if not plan or not plan.enabled:
        raise bad_request(f"方案不存在或未启用: {plan_code}")

    await quota_service.consume_for_check(db, user, cost_points=1)
    from engine import __version__ as engine_version

    task = await check_task_repo.create(
        db,
        user.id,
        plan_code,
        old_task.file_name,
        old_task.file_size,
        old_task.word_count,
        engine_version,
    )
    await db.commit()
    await run_check_job.enqueue_recheck(db, task.id, old_task.id, plan.params_json or {})
    return _summary_of(task)


def _summary_of(task) -> CheckTaskSummary:
    return CheckTaskSummary(
        task_id=task.id,
        status=task.status,
        progress=100 if task.status == "succeeded" else None,
        plan_code=task.plan_code,
        file_name=task.file_name,
        created_at=task.created_at,
    )
