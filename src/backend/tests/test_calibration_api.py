"""校准端点测试：回传报告配对（AC-14）、校准状态（AC-15）、用量（AC-13）。"""

from tests.conftest import SAMPLE_TEXT


async def _create_done_check(client, headers):
    files = {"file": ("sample.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
    resp = await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "cnki_sim"})
    return resp.json()["data"]["task_id"]


async def test_submit_calibration_report(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="cal@example.com")
    task_id = await _create_done_check(client, headers)
    files = {"file": ("report.pdf", b"%PDF-1.4 fake report", "application/pdf")}
    data = {"platform": "cnki", "real_rate": "42.5", "task_id": str(task_id)}
    resp = await client.post("/api/v1/calibration/reports", headers=headers, files=files, data=data)
    assert resp.status_code == 201, resp.text
    rd = resp.json()["data"]
    assert rd["sample_id"] > 0
    assert rd["status"] == "pending_validation"


async def test_submit_calibration_invalid_rate(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="calbad@example.com")
    task_id = await _create_done_check(client, headers)
    files = {"file": ("report.pdf", b"%PDF", "application/pdf")}
    resp = await client.post(
        "/api/v1/calibration/reports",
        headers=headers,
        files=files,
        data={"platform": "cnki", "real_rate": "150", "task_id": str(task_id)},
    )
    assert resp.status_code == 400


async def test_submit_calibration_unmatched_task(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="calnone@example.com")
    files = {"file": ("report.pdf", b"%PDF", "application/pdf")}
    resp = await client.post(
        "/api/v1/calibration/reports",
        headers=headers,
        files=files,
        data={"platform": "cnki", "real_rate": "10", "task_id": "99999"},
    )
    assert resp.status_code == 404


async def test_calibration_status_cold_start(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="calstat@example.com")
    resp = await client.get("/api/v1/calibration/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "sample_count" in data
    assert data["model_status"] in ("cold_start", "linear")


async def test_usage_endpoint(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="usage2@example.com")
    resp = await client.get("/api/v1/users/me/usage", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["free_quota"] >= 5
    assert data["points"] >= 0
