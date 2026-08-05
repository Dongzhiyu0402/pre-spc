"""pytest 全局夹具。

- 环境变量必须在 import app 之前设置（PRE_ 前缀）。
- 使用 SQLite 文件库 + 同步 RQ（PRE_RQ_SYNC=1），不依赖 Postgres/Redis。
"""

import os
import sys
from pathlib import Path

# 保证 engine 与 backend 可导入（src/ 同级）
SRC_DIR = Path(__file__).resolve().parent.parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

TEST_DB = str(SRC_DIR / "backend" / ".test_db.sqlite")

os.environ["PRE_DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["PRE_RQ_SYNC"] = "1"
os.environ["PRE_AUTO_CREATE_TABLES"] = "0"
os.environ["PRE_JWT_SECRET"] = "test-secret-not-for-prod"
os.environ["PRE_STORAGE_DIR"] = str(SRC_DIR / "backend" / ".test_storage")
os.environ["PRE_REPORT_DIR"] = str(SRC_DIR / "backend" / ".test_reports")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.database import engine, SessionLocal, init_models  # noqa: E402
from app.main import app  # noqa: E402
from app.repositories import plan_repo  # noqa: E402

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
if os.path.exists(os.environ["PRE_STORAGE_DIR"]):
    import shutil

    shutil.rmtree(os.environ["PRE_STORAGE_DIR"], ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
async def _setup_db():
    await init_models()
    async with SessionLocal() as db:
        await plan_repo.seed_defaults(db)
        await db.commit()
    yield
    await engine.dispose()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """每个测试前重置内存限流器，避免跨测试污染（敏感端点 10 次/分钟）。"""
    from app.core.rate_limit import _rate_limiter

    _rate_limiter._hits.clear()
    yield


@pytest.fixture
def auth_headers_factory():
    """注册并返回 (headers, email, password) 的工具。"""

    async def _factory(client: AsyncClient, email: str = "u@example.com", password: str = "Test@1234"):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "nickname": "tester"},
        )
        assert resp.status_code == 201, resp.text
        tokens = resp.json()["data"]["tokens"]
        return {"Authorization": f"Bearer {tokens['access_token']}"}, tokens, email, password

    return _factory


SAMPLE_TEXT = "随着信息技术的快速发展，教育信息化已经成为当代高等教育改革的重要方向之一。"


def make_txt(name: str = "sample.txt") -> tuple[str, bytes]:
    return name, SAMPLE_TEXT.encode("utf-8")
