"""FastAPI 入口：只装配（挂中间件、include_router、启动），不写业务。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, calibration, checks, plans, usage
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger, setup_logging
from app.core.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    if settings.auto_create_tables:
        from app.database import init_models

        await init_models()
        from app.database import SessionLocal
        from app.repositories import plan_repo

        async with SessionLocal() as db:
            await plan_repo.seed_defaults(db)
            await db.commit()
    logger.info("app started: %s", settings.app_name)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        max_age=86400,
    )
    app.add_middleware(RateLimitMiddleware)

    register_exception_handlers(app)

    app.include_router(auth.router)
    app.include_router(plans.router)
    app.include_router(checks.router)
    app.include_router(calibration.router)
    app.include_router(usage.router)

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict:
        return {"code": 0, "data": {"status": "ok"}, "message": "ok"}

    return app


app = create_app()
