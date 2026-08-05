"""SQLAlchemy 基类与表元数据（与 api/schema.sql 对齐）。"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, JSON, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 可移植 JSON 类型：Postgres 用 JSONB，SQLite 测试退化为 JSON
JSONVariant = JSON().with_variant(JSONB, "postgresql")
# 可移植主键：Postgres 用 BIGSERIAL，SQLite 用 INTEGER PRIMARY KEY（否则不自增）
IdVariant = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    """统一基类：id + created_at + updated_at。"""

    id: Mapped[int] = mapped_column(IdVariant, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
