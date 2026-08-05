"""异步数据库引擎与会话工厂（SQLAlchemy 2.0 + asyncpg / aiosqlite 测试）。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：请求级会话。"""
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """建表（开发/测试用；生产走 schema.sql / alembic）。"""
    from app.models import Base  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.plan  # noqa: F401
    import app.models.check_task  # noqa: F401
    import app.models.check_result  # noqa: F401
    import app.models.check_segment  # noqa: F401
    import app.models.calibration_sample  # noqa: F401
    import app.models.calibration_model  # noqa: F401
    import app.models.point_transaction  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
