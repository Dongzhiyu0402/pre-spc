"""plans 查重方案表模型（可配置，AC-11）。"""

from sqlalchemy import text, Boolean, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, JSONVariant


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (CheckConstraint("type IN ('engine', 'api')", name="chk_plans_type"),)

    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    params_json: Mapped[dict] = mapped_column(JSONVariant, nullable=False, server_default="{}")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
