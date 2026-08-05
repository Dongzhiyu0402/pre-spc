"""校准训练服务测试（AC-15：样本 >= 30 触发模型训练并更新预估区间参数）。"""

import pytest

from app.repositories import calibration_repo, check_result_repo, check_task_repo
from app.services import calibration_service


async def _seed_samples(db, platform: str, count: int, raw: float = 50.0, real: float = 45.0):
    """直接插入 count 条已验证样本 + 关联任务/结果。"""
    from decimal import Decimal

    from app.models.calibration_sample import CalibrationSample
    from app.models.check_result import CheckResult
    from app.models.check_task import CheckTask
    from app.models.user import User

    user = User(email=f"train_{platform}@example.com", password_hash="x", nickname="trainer", free_quota=5, points=0)
    db.add(user)
    await db.flush()
    for i in range(count):
        task = CheckTask(
            user_id=user.id, plan_code="cnki_sim", file_name="a.txt", file_size=10,
            word_count=100, status="succeeded", engine_version="0.1.0",
        )
        db.add(task)
        await db.flush()
        result = CheckResult(
            task_id=task.id, raw_score=Decimal(str(raw)), est_median=Decimal("45.0"),
            est_low=Decimal("30.0"), est_high=Decimal("60.0"), confidence=Decimal("50.0"),
            segments_json=[],
        )
        db.add(result)
        sample = CalibrationSample(
            user_id=user.id, task_id=task.id, platform=platform,
            real_rate=Decimal(str(real)), report_file="r.pdf", validated=True,
        )
        db.add(sample)
    await db.commit()


async def test_train_triggered_at_30(client, auth_headers_factory, tmp_path, monkeypatch):
    """样本达 30 后 train_if_enough 训练出 linear 模型并写入桶文件。"""
    from app.config import settings

    # engine_model_dir 优先于默认目录（property resolved_engine_model_dir 读取它）
    monkeypatch.setattr(settings, "engine_model_dir", str(tmp_path))

    from app.database import SessionLocal

    async with SessionLocal() as db:
        await _seed_samples(db, "cnki", 30, raw=50.0, real=45.0)

    async with SessionLocal() as db:
        trained = await calibration_service.train_if_enough(db, "cnki", "undergrad", threshold=30)
    assert trained is True

    import os

    bucket_file = os.path.join(str(tmp_path), "cnki_undergrad.json")
    assert os.path.exists(bucket_file)

    async with SessionLocal() as db:
        status = await calibration_service.get_status(db, "cnki", "undergrad")
    assert status.model_status == "linear"
    assert status.sample_count >= 30


async def test_train_not_triggered_below_30(client, auth_headers_factory, tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "engine_model_dir", str(tmp_path))
    from app.database import SessionLocal

    async with SessionLocal() as db:
        await _seed_samples(db, "vip", 10, raw=50.0, real=45.0)
    async with SessionLocal() as db:
        trained = await calibration_service.train_if_enough(db, "vip", "undergrad", threshold=30)
    assert trained is False

    import os

    assert not os.path.exists(os.path.join(str(tmp_path), "vip_undergrad.json"))
