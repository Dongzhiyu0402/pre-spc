"""users 用户表模型。"""

from sqlalchemy import CheckConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="chk_users_role"),
        CheckConstraint("free_quota >= 0", name="chk_users_free_quota"),
        CheckConstraint("points >= 0", name="chk_users_points"),
    )

    email: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    nickname: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default="user")
    free_quota: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    points: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
