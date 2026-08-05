"""calibration_samples 校准样本表模型（AC-14）。"""

from decimal import Decimal

from sqlalchemy import text, BigInteger, Boolean, CheckConstraint, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class CalibrationSample(Base):
    __tablename__ = "calibration_samples"
    __table_args__ = (
        CheckConstraint("platform IN ('cnki', 'vip', 'wanfang')", name="chk_calibration_samples_platform"),
        CheckConstraint("real_rate >= 0 AND real_rate <= 100", name="chk_calibration_samples_real_rate"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("check_tasks.id"), nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    real_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    report_file: Mapped[str] = mapped_column(Text, nullable=False)
    validated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
