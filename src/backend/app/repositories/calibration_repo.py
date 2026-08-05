"""calibration 相关查询封装。"""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calibration_model import CalibrationModel
from app.models.calibration_sample import CalibrationSample


async def create_sample(
    db: AsyncSession,
    user_id: int,
    task_id: int,
    platform: str,
    real_rate: Decimal,
    report_file: str,
) -> CalibrationSample:
    sample = CalibrationSample(
        user_id=user_id,
        task_id=task_id,
        platform=platform,
        real_rate=real_rate,
        report_file=report_file,
        validated=False,
    )
    db.add(sample)
    await db.flush()
    return sample


async def count_validated(db: AsyncSession, platform: str | None = None) -> int:
    stmt = select(func.count()).select_from(CalibrationSample).where(CalibrationSample.validated.is_(True))
    if platform:
        stmt = stmt.where(CalibrationSample.platform == platform)
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def list_validated_samples(db: AsyncSession, platform: str) -> list[CalibrationSample]:
    result = await db.execute(
        select(CalibrationSample)
        .where(CalibrationSample.validated.is_(True), CalibrationSample.platform == platform)
        .order_by(CalibrationSample.created_at)
    )
    return list(result.scalars().all())


async def get_model(db: AsyncSession, platform: str, paper_type: str) -> CalibrationModel | None:
    result = await db.execute(
        select(CalibrationModel).where(
            CalibrationModel.platform == platform, CalibrationModel.paper_type == paper_type
        )
    )
    return result.scalar_one_or_none()


async def upsert_model(
    db: AsyncSession,
    platform: str,
    paper_type: str,
    sample_count: int,
    model_version: str,
    mae: Decimal | None,
    params_json: dict,
) -> CalibrationModel:
    model = await get_model(db, platform, paper_type)
    if model is None:
        model = CalibrationModel(
            platform=platform,
            paper_type=paper_type,
            sample_count=sample_count,
            model_version=model_version,
            mae=mae,
            params_json=params_json,
            trained_at=func.now(),
        )
        db.add(model)
    else:
        model.sample_count = sample_count
        model.model_version = model_version
        model.mae = mae
        model.params_json = params_json
        model.trained_at = func.now()
    await db.flush()
    return model
