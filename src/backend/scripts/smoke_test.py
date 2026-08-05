"""全端点冒烟测试：覆盖 openapi.yaml 14 个端点（注册/登录/刷新/me/plans/checks 系列/校准/用量）。

运行：PYTHONPATH=.. python scripts/smoke_test.py
依赖：SQLite 测试库 + 同步 RQ（PRE_RQ_SYNC=1），无需 Postgres/Redis。
"""

import asyncio
import os
import sys
import tempfile
import uuid
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(BACKEND))

# 每次运行使用独立临时目录，避免清理旧文件（沙箱禁止删除）
_TMP = tempfile.mkdtemp(prefix="prespc_smoke_")
_RUN_ID = uuid.uuid4().hex[:8]

os.environ["PRE_DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP}/smoke_{_RUN_ID}.sqlite"
os.environ["PRE_RQ_SYNC"] = "1"
os.environ["PRE_AUTO_CREATE_TABLES"] = "1"
os.environ["PRE_JWT_SECRET"] = "smoke-test-secret-0123456789abcdef"
os.environ["PRE_STORAGE_DIR"] = os.path.join(_TMP, "storage")
os.environ["PRE_REPORT_DIR"] = os.path.join(_TMP, "reports")

import httpx  # noqa: E402

SAMPLE = "随着信息技术的快速发展，教育信息化已经成为当代高等教育改革的重要方向之一。"
CHECKLIST: list[tuple[str, str, callable]] = []


def check(name: str, method: str, path: str):
    def deco(fn):
        CHECKLIST.append((name, f"{method} {path}", fn))
        return fn

    return deco


@check("register", "POST", "/api/v1/auth/register")
async def _(c, r):
    resp = await c.post(
        "/api/v1/auth/register",
        json={"email": "smoke@example.com", "password": "Test@1234", "nickname": "smoke"},
    )
    assert resp.status_code == 201, resp.text
    r["user"] = resp.json()["data"]["user"]
    r["tokens"] = resp.json()["data"]["tokens"]
    r["headers"] = {"Authorization": f"Bearer {r['tokens']['access_token']}"}
    assert r["user"]["free_quota"] >= 5


@check("login", "POST", "/api/v1/auth/login")
async def _(c, r):
    resp = await c.post("/api/v1/auth/login", json={"email": "smoke@example.com", "password": "Test@1234"})
    assert resp.status_code == 200, resp.text
    r["tokens"] = resp.json()["data"]["tokens"]
    r["headers"] = {"Authorization": f"Bearer {r['tokens']['access_token']}"}
    assert r["tokens"]["access_token"]


@check("refresh", "POST", "/api/v1/auth/refresh")
async def _(c, r):
    resp = await c.post("/api/v1/auth/refresh", json={"refresh_token": r["tokens"]["refresh_token"]})
    assert resp.status_code == 200, resp.text
    # refresh 响应 data 即 TokensOut（access_token 直接挂 data 下）
    r["tokens"] = resp.json()["data"]
    r["headers"] = {"Authorization": f"Bearer {r['tokens']['access_token']}"}


@check("me", "GET", "/api/v1/auth/me")
async def _(c, r):
    resp = await c.get("/api/v1/auth/me", headers=r["headers"])
    assert resp.status_code == 200 and resp.json()["data"]["email"] == "smoke@example.com"


@check("plans", "GET", "/api/v1/plans")
async def _(c, r):
    resp = await c.get("/api/v1/plans", headers=r["headers"])
    assert resp.status_code == 200
    codes = [p["code"] for p in resp.json()["data"]]
    assert "cnki_sim" in codes and "api_placeholder" in codes


@check("create check", "POST", "/api/v1/checks")
async def _(c, r):
    files = {"file": ("sample.txt", SAMPLE.encode("utf-8"), "text/plain")}
    resp = await c.post("/api/v1/checks", headers=r["headers"], files=files, data={"plan_code": "cnki_sim"})
    assert resp.status_code == 202, resp.text
    r["task_id"] = resp.json()["data"]["task_id"]


@check("check status", "GET", "/api/v1/checks/{id}")
async def _(c, r):
    resp = await c.get(f"/api/v1/checks/{r['task_id']}", headers=r["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "succeeded"


@check("report", "GET", "/api/v1/checks/{id}/report")
async def _(c, r):
    resp = await c.get(f"/api/v1/checks/{r['task_id']}/report", headers=r["headers"])
    assert resp.status_code == 200, resp.text
    d = resp.json()["data"]
    assert d["est_low"] <= d["est_median"] <= d["est_high"]
    assert "非官方检测报告" in d["disclaimer"]


@check("export html", "GET", "/api/v1/checks/{id}/export?format=html")
async def _(c, r):
    resp = await c.get(f"/api/v1/checks/{r['task_id']}/export?format=html", headers=r["headers"])
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


@check("history", "GET", "/api/v1/checks")
async def _(c, r):
    resp = await c.get("/api/v1/checks?page=1&limit=10", headers=r["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


@check("recheck", "POST", "/api/v1/checks/{id}/recheck")
async def _(c, r):
    resp = await c.post(
        f"/api/v1/checks/{r['task_id']}/recheck", headers=r["headers"], json={"plan_code": "vip_sim"}
    )
    assert resp.status_code == 202, resp.text
    r["recheck_id"] = resp.json()["data"]["task_id"]
    assert r["recheck_id"] != r["task_id"]


@check("calibration submit", "POST", "/api/v1/calibration/reports")
async def _(c, r):
    files = {"file": ("report.pdf", b"%PDF-1.4 smoke", "application/pdf")}
    data = {"platform": "cnki", "real_rate": "45.5", "task_id": str(r["task_id"])}
    resp = await c.post("/api/v1/calibration/reports", headers=r["headers"], files=files, data=data)
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["status"] == "pending_validation"


@check("calibration status", "GET", "/api/v1/calibration/status")
async def _(c, r):
    resp = await c.get("/api/v1/calibration/status", headers=r["headers"])
    assert resp.status_code == 200
    assert "sample_count" in resp.json()["data"]


@check("usage", "GET", "/api/v1/users/me/usage")
async def _(c, r):
    resp = await c.get("/api/v1/users/me/usage", headers=r["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["free_quota"] < 5  # 已消耗


async def main() -> int:
    from httpx import ASGITransport, AsyncClient
    from app.database import SessionLocal, init_models
    from app.main import app
    from app.repositories import plan_repo

    # ASGITransport 不触发 lifespan，需显式建表 + 种子方案
    await init_models()
    async with SessionLocal() as db:
        await plan_repo.seed_defaults(db)
        await db.commit()

    transport = ASGITransport(app=app)
    passed = 0
    async with AsyncClient(transport=transport, base_url="http://smoke") as c:
        r: dict = {}
        print("== 预查重项目 全端点冒烟测试 ==")
        for name, route, fn in CHECKLIST:
            try:
                await fn(c, r)
                print(f"  [PASS] {name:<22} {route}")
                passed += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  [FAIL] {name:<22} {route}  -> {exc}")
    total = len(CHECKLIST)
    print(f"== 结果: {passed}/{total} 通过 ==")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
