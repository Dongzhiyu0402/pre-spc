"""check_segments 命中片段表模型（报告高亮）。"""

from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class CheckSegment(Base):
    __tablename__ = "check_segments"
    __table_args__ = (
        CheckConstraint("highlight_type IN ('high', 'mid', 'cite')", name="chk_check_segments_highlight_type"),
        CheckConstraint("start_offset >= 0", name="chk_check_segments_start"),
        CheckConstraint("end_offset > start_offset", name="chk_check_segments_offset"),
        CheckConstraint("similarity >= 0 AND similarity <= 100", name="chk_check_segments_similarity"),
    )

    result_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("check_results.id"), nullable=False)
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    highlight_type: Mapped[str] = mapped_column(Text, nullable=False)
    matched_source: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    similarity: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
