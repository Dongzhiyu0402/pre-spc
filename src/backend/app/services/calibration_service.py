"""校准业务：回传样本解析配对（AC-14）、模型训练触发（AC-15）。"""

import os
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import bad_request, not_found
from app.models.user import User
from app.repositories import calibration_repo, check_task_repo
from app.schemas.report import CalibrationStatusOut
from app.services import quota_service

ALLOWED_REPORT_EXT = {".pdf", ".html", ".htm", ".docx"}
_MODEL_VERSION = "v0.1.0"


async def submit_report(
    db: AsyncSession,
    user: User,
    file_name: str,
    content: bytes,
    platform: str,
    real_rate: float,
    task_id: int,
) -> int:
    """回传真实查重报告：校验 -> 与预查重任务配对 -> 入库（AC-14）。"""
    if platform not in ("cnki", "vip", "wanfang"):
        raise bad_request(f"不支持的平台: {platform}")
    if not (0 <= real_rate <= 100):
        raise bad_request("真实查重率必须在 0-100 之间")
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_REPORT_EXT:
        raise bad_request("报告文件仅支持 pdf/html/docx")
    if len(content) > 20 * 1024 * 1024:
        raise bad_request("报告文件超过 20MB 限制")

    task = await check_task_repo.get_by_id(db, task_id)
    if not task or task.user_id != user.id:
        raise not_found("关联的预查重任务不存在或无权访问")
    if task.status != "succeeded":
        raise bad_request("关联任务尚未完成，无法配对")

    report_dir = os.path.join(settings.storage_dir, "calibration")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"sample_{user.id}_{task_id}{ext}")
    with open(report_path, "wb") as fh:
        fh.write(content)

    sample = await calibration_repo.create_sample(
        db, user.id, task_id, platform, Decimal(str(round(real_rate, 2))), report_path
    )
    await quota_service.reward_calibration(db, user, settings.calibration_reward_points)
    await db.commit()
    return sample.id


async def get_status(db: AsyncSession, platform: str = "cnki", paper_type: str = "undergrad") -> CalibrationStatusOut:
    sample_count = await calibration_repo.count_validated(db, platform)
    model = await calibration_repo.get_model(db, platform, paper_type)
    if model and model.sample_count >= 30:
        return CalibrationStatusOut(
            sample_count=sample_count,
            model_version=model.model_version,
            mae=float(model.mae) if model.mae is not None else None,
            model_status="linear",
        )
    return CalibrationStatusOut(sample_count=sample_count, model_version=None, mae=None, model_status="cold_start")


async def train_if_enough(db: AsyncSession, platform: str = "cnki", paper_type: str = "undergrad", threshold: int = 30) -> bool:
    """样本 >= threshold 触发模型训练并写入（AC-15）。

    使用 engine 的线性回归（纯 Python 实现），按 (平台, 论文类型) 分桶不混训。
    """
    samples = await calibration_repo.list_validated_samples(db, platform)
    if len(samples) < threshold:
        return False
    # 真实配对：取每个 sample 关联任务的结果 raw_score
    from app.repositories import check_result_repo

    true_pairs: list[tuple[float, float]] = []
    for s in samples:
        result = await check_result_repo.get_by_task_id(db, s.task_id)
        if result is not None:
            true_pairs.append((float(result.raw_score), float(s.real_rate)))
    if len(true_pairs) < threshold:
        return False

    from engine.calibration.linear import train_linear_model
    from engine.calibration.model_store import save_bucket_model

    model = train_linear_model(true_pairs)
    payload = model.to_dict()
    save_bucket_model(settings.resolved_engine_model_dir, platform, paper_type, payload)
    await calibration_repo.upsert_model(
        db,
        platform,
        paper_type,
        sample_count=len(true_pairs),
        model_version=_MODEL_VERSION,
        mae=Decimal(str(round(model.mae, 2))),
        params_json=payload,
    )
    await db.commit()
    return True
