"""check_results 查重结果表模型（1:1 with check_tasks）。"""

from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, JSONVariant


class CheckResult(Base):
    __tablename__ = "check_results"
    __table_args__ = (
        CheckConstraint("raw_score >= 0 AND raw_score <= 100", name="chk_check_results_raw_score"),
        CheckConstraint("est_median >= 0 AND est_median <= 100", name="chk_check_results_est_median"),
        CheckConstraint("est_low >= 0 AND est_low <= 100", name="chk_check_results_est_low"),
        CheckConstraint("est_high >= 0 AND est_high <= 100", name="chk_check_results_est_high"),
        CheckConstraint("confidence >= 0 AND confidence <= 100", name="chk_check_results_confidence"),
        # 区间一致性：low <= median <= high（防沉默逻辑错误）
        CheckConstraint("est_low <= est_median AND est_median <= est_high", name="chk_check_results_interval"),
    )

    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("check_tasks.id"), nullable=False, unique=True)
    raw_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    est_median: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    est_low: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    est_high: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    segments_json: Mapped[list] = mapped_column(JSONVariant, nullable=False, server_default="[]")
