"""calibration_models 校准模型表模型（按 平台+论文类型 分桶）。"""

from decimal import Decimal
from datetime import datetime

from sqlalchemy import CheckConstraint, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, JSONVariant


class CalibrationModel(Base):
    __tablename__ = "calibration_models"
    __table_args__ = (
        CheckConstraint("platform IN ('cnki', 'vip', 'wanfang')", name="chk_calibration_models_platform"),
        CheckConstraint("paper_type IN ('undergrad', 'postgrad', 'journal')", name="chk_calibration_models_paper_type"),
        CheckConstraint("sample_count >= 0", name="chk_calibration_models_sample_count"),
        UniqueConstraint("platform", "paper_type", name="uk_calibration_models_bucket"),
    )

    platform: Mapped[str] = mapped_column(Text, nullable=False)
    paper_type: Mapped[str] = mapped_column(Text, nullable=False, server_default="undergrad")
    sample_count: Mapped[int] = mapped_column(nullable=False, server_default="0")
    model_version: Mapped[str] = mapped_column(Text, nullable=False)
    mae: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    params_json: Mapped[dict] = mapped_column(JSONVariant, nullable=False, server_default="{}")
    trained_at: Mapped[datetime | None] = mapped_column(nullable=True)
