"""查重端点测试：上传/状态/报告/历史/再检测/用量（AC-01/03/04/05/13）。"""

from tests.conftest import SAMPLE_TEXT


async def test_plans_list(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="plans@example.com")
    resp = await client.get("/api/v1/plans", headers=headers)
    assert resp.status_code == 200
    codes = [p["code"] for p in resp.json()["data"]]
    assert "cnki_sim" in codes
    assert "vip_sim" in codes


async def test_create_check_sync_success(client, auth_headers_factory):
    """上传 -> 同步查重 -> 状态 succeeded -> 报告完整（AC-01/05）。"""
    headers, *_ = await auth_headers_factory(client, email="check@example.com")
    files = {"file": ("sample.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
    data = {"plan_code": "cnki_sim"}
    resp = await client.post("/api/v1/checks", headers=headers, files=files, data=data)
    assert resp.status_code == 202, resp.text
    task_id = resp.json()["data"]["task_id"]

    detail = await client.get(f"/api/v1/checks/{task_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["status"] == "succeeded"

    report = await client.get(f"/api/v1/checks/{task_id}/report", headers=headers)
    assert report.status_code == 200
    rd = report.json()["data"]
    for key in ("est_median", "est_low", "est_high", "confidence", "segments", "sources", "disclaimer"):
        assert key in rd
    assert rd["est_low"] <= rd["est_median"] <= rd["est_high"]
    assert "非官方检测报告" in rd["disclaimer"]
    # UI 扩展字段（联调阻塞项）：full_text / metrics / chapters / source_detail
    assert rd["full_text"] is not None and rd["full_text"] != ""
    assert rd["metrics"] is not None
    assert set(rd["metrics"]) == {"exclude_cite_rate", "exclude_self_rate", "max_single_source_rate"}
    assert rd["metrics"]["exclude_self_rate"] is None
    assert isinstance(rd["chapters"], list) and len(rd["chapters"]) >= 1
    assert "title" in rd["chapters"][0] and "rate" in rd["chapters"][0]
    seg0 = rd["segments"][0] if rd["segments"] else {}
    assert "source_detail" in seg0


async def test_create_check_invalid_plan(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="badplan@example.com")
    files = {"file": ("sample.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
    resp = await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "no_such"})
    assert resp.status_code == 400


async def test_create_check_empty_file_does_not_consume(client, auth_headers_factory):
    """AC-03：空文件返回明确错误且不消耗次数。"""
    headers, *_ = await auth_headers_factory(client, email="empty@example.com")
    before = (await client.get("/api/v1/users/me/usage", headers=headers)).json()["data"]
    files = {"file": ("empty.txt", b"", "text/plain")}
    resp = await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "cnki_sim"})
    assert resp.status_code == 400
    after = (await client.get("/api/v1/users/me/usage", headers=headers)).json()["data"]
    assert after["free_quota"] == before["free_quota"]


async def test_create_check_unsupported_type(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="exe@example.com")
    files = {"file": ("virus.exe", b"MZ...", "application/octet-stream")}
    resp = await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "cnki_sim"})
    assert resp.status_code == 400


async def test_usage_deduction(client, auth_headers_factory):
    """AC-04/13：查重后免费次数减少，积分优先扣除。"""
    headers, *_ = await auth_headers_factory(client, email="usage@example.com")
    before = (await client.get("/api/v1/users/me/usage", headers=headers)).json()["data"]
    files = {"file": ("sample.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
    await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "cnki_sim"})
    after = (await client.get("/api/v1/users/me/usage", headers=headers)).json()["data"]
    assert after["free_quota"] == before["free_quota"] - 1
    assert after["points"] == before["points"]


async def test_history_pagination(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="hist@example.com")
    for i in range(3):
        files = {"file": (f"s{i}.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
        await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "cnki_sim"})
    resp = await client.get("/api/v1/checks?page=1&limit=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 2
    assert data["total"] >= 3
    assert data["hasMore"] is True


async def test_report_requires_owner(client, auth_headers_factory):
    headers_a, *_ = await auth_headers_factory(client, email="owner_a@example.com")
    headers_b, *_ = await auth_headers_factory(client, email="owner_b@example.com")
    files = {"file": ("sample.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
    resp = await client.post("/api/v1/checks", headers=headers_a, files=files, data={"plan_code": "cnki_sim"})
    task_id = resp.json()["data"]["task_id"]
    other = await client.get(f"/api/v1/checks/{task_id}/report", headers=headers_b)
    assert other.status_code == 404


async def test_export_html(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="exp@example.com")
    files = {"file": ("sample.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
    resp = await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "cnki_sim"})
    task_id = resp.json()["data"]["task_id"]
    export = await client.get(f"/api/v1/checks/{task_id}/export?format=html", headers=headers)
    assert export.status_code == 200
    assert "text/html" in export.headers["content-type"]
    assert "非官方检测报告" in export.text


async def test_recheck_new_task(client, auth_headers_factory):
    headers, *_ = await auth_headers_factory(client, email="recheck@example.com")
    files = {"file": ("sample.txt", SAMPLE_TEXT.encode("utf-8"), "text/plain")}
    resp = await client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": "cnki_sim"})
    task_id = resp.json()["data"]["task_id"]
    rr = await client.post(
        f"/api/v1/checks/{task_id}/recheck", headers=headers, json={"plan_code": "vip_sim"}
    )
    assert rr.status_code == 202
    new_id = rr.json()["data"]["task_id"]
    assert new_id != task_id
    detail = await client.get(f"/api/v1/checks/{new_id}", headers=headers)
    assert detail.json()["data"]["status"] == "succeeded"
    assert detail.json()["data"]["plan_code"] == "vip_sim"
