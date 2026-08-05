"""check_tasks 查重任务表模型。"""

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class CheckTask(Base):
    __tablename__ = "check_tasks"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'succeeded', 'failed')", name="chk_check_tasks_status"),
        CheckConstraint("file_size >= 0", name="chk_check_tasks_file_size"),
        CheckConstraint("word_count >= 0 AND word_count <= 100000", name="chk_check_tasks_word_count"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    plan_code: Mapped[str] = mapped_column(Text, ForeignKey("plans.code"), nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    engine_version: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
