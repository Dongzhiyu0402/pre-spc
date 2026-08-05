"""应用配置（pydantic-settings，env 驱动）。

环境变量前缀 PRE_（如 PRE_DATABASE_URL）。测试可用 PRE_DATABASE_URL=sqlite+aiosqlite:///...
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PRE_", env_file=".env", extra="ignore")

    app_name: str = "pre-spc-api"
    debug: bool = False
    auto_create_tables: bool = True

    # 数据库
    database_url: str = "postgresql+asyncpg://pre:pre@localhost:5432/pre_spc"
    # Redis / RQ
    redis_url: str = "redis://localhost:6379/0"
    rq_queue_name: str = "checks"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # 用量（AC-12/13）
    register_free_quota: int = 5
    check_cost_points: int = 1
    calibration_reward_points: int = 2

    # 上传限制（Spec §10：单文件 ≤50MB / ≤10 万字）
    max_upload_mb: int = 50
    max_word_count: int = 100000

    # 引擎模型目录
    engine_index_dir: str = ""
    engine_model_dir: str = ""

    # 文档原文存储（本地卷；生产应加密 + 30 天清理，见 directory-structure §6）
    storage_dir: str = "./storage"
    report_dir: str = "./reports"

    # CORS（前后端分离）
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def resolved_engine_index_dir(self) -> str:
        if self.engine_index_dir:
            return self.engine_index_dir
        from pathlib import Path

        return str(Path(__file__).resolve().parent.parent.parent / "engine" / "models" / "corpus_index")

    @property
    def resolved_engine_model_dir(self) -> str:
        if self.engine_model_dir:
            return self.engine_model_dir
        from pathlib import Path

        return str(Path(__file__).resolve().parent.parent.parent / "engine" / "models" / "calibration")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
