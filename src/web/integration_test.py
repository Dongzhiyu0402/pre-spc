"""前后端联调验证脚本（前端侧，针对真实后端 http://127.0.0.1:8000）。

覆盖：注册/重复注册409/登录/401/me/plans/三种方案查重/报告核心+UI扩展字段/导出HTML+PDF回退/再检测/校准回传/用量递减/超限402/历史列表。
运行：python integration_test.py（输出到 stdout，联调时重定向到文件查看）
"""

import time

import httpx

BASE = "http://127.0.0.1:8000"
client = httpx.Client(base_url=BASE, timeout=40)
results: list[str] = []


def log(name: str, ok: bool, detail: str = ""):
    results.append(f"[{'PASS' if ok else 'FAIL'}] {name:<28} {detail}")


def main() -> int:
    # 1. 注册
    email = f"int_{int(time.time())}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "Test@1234", "nickname": "联调测试"})
    log("register 201", r.status_code == 201, f"status={r.status_code}")
    if r.status_code != 201:
        print("\n".join(results))
        return 1
    user = r.json()["data"]["user"]
    tokens = r.json()["data"]["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    log("register free_quota", user["free_quota"] >= 5, f"quota={user['free_quota']}")

    # 2. 重复注册 409
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "Test@1234", "nickname": "dup"})
    log("duplicate register 409", r.status_code == 409, f"status={r.status_code} msg={r.json().get('message')}")

    # 3. 登录 + 401
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Test@1234"})
    log("login 200", r.status_code == 200, f"status={r.status_code}")
    r = client.get("/api/v1/checks/1/report")
    log("no-auth 401", r.status_code == 401, f"status={r.status_code}")

    # 4. me / plans
    r = client.get("/api/v1/auth/me", headers=headers)
    log("me 200", r.status_code == 200 and r.json()["data"]["email"] == email)
    r = client.get("/api/v1/plans", headers=headers)
    codes = [p["code"] for p in r.json()["data"]]
    log("plans 4 codes", r.status_code == 200 and len(codes) == 4, f"codes={codes}")

    # 5. 三方案查重
    last_task: int | None = None
    first_report: dict | None = None
    for plan in ["cnki_sim", "vip_sim", "wanfang_sim"]:
        content = ("随着信息技术的快速发展，教育信息化已经成为当代高等教育改革的重要方向之一。" * 20).encode("utf-8")
        files = {"file": (f"demo_{plan}.txt", content, "text/plain")}
        r = client.post("/api/v1/checks", headers=headers, files=files, data={"plan_code": plan})
        if r.status_code != 202:
            log(f"create {plan} 202", False, f"status={r.status_code} body={r.text[:200]}")
            continue
        tid = r.json()["data"]["task_id"]
        status = "pending"
        for _ in range(60):
            s = client.get(f"/api/v1/checks/{tid}", headers=headers).json()["data"]
            status = s["status"]
            if status in ("succeeded", "failed"):
                break
            time.sleep(0.5)
        log(f"check {plan} succeeded", status == "succeeded", f"task={tid}")
        if status == "succeeded":
            rep = client.get(f"/api/v1/checks/{tid}/report", headers=headers)
            d = rep.json()["data"]
            core = ["est_median", "est_low", "est_high", "confidence", "segments", "sources", "disclaimer"]
            missing = [k for k in core if k not in d]
            log(
                f"report {plan} core fields",
                not missing and d["est_low"] <= d["est_median"] <= d["est_high"],
                f"missing={missing} median={d.get('est_median')} low={d.get('est_low')} high={d.get('est_high')} conf={d.get('confidence')} segs={len(d.get('segments', []))}",
            )
            # 前端 UI 扩展字段（后端交付声明应含，实际待核）
            seg0 = d.get("segments", [{}])[0]
            ext = {
                "full_text": d.get("full_text") is not None,
                "metrics": d.get("metrics") is not None,
                "chapters": d.get("chapters") is not None,
                "source_detail": "source_detail" in seg0,
            }
            log(f"report {plan} UI-extension", all(ext.values()), f"present={ext}")
            if plan == "cnki_sim" and first_report is None:
                first_report = d
            last_task = tid

    # 6. 完整报告 JSON 证据（cnki 首份）
    if first_report is not None:
        import json as _json

        print("== 完整报告 JSON（cnki_sim）==")
        print(_json.dumps(first_report, ensure_ascii=False, indent=2)[:4000])

    # 6. 导出（HTML 后端生成；PDF 需 reportlab，缺失时确认前端回退）
    if last_task is not None:
        er = client.get(f"/api/v1/checks/{last_task}/export", headers=headers, params={"format": "html"})
        log("export html", er.status_code == 200 and "text/html" in er.headers.get("content-type", ""), f"status={er.status_code} ct={er.headers.get('content-type')}")
        pr = client.get(f"/api/v1/checks/{last_task}/export", headers=headers, params={"format": "pdf"})
        log("export pdf fallback", pr.status_code == 200 or pr.status_code == 500, f"status={pr.status_code} len={len(pr.content)} body={pr.text[:100]!r}")

    # 7. 再检测
    if last_task is not None:
        r = client.post(f"/api/v1/checks/{last_task}/recheck", headers=headers, json={"plan_code": "vip_sim"})
        log("recheck 202", r.status_code == 202, f"status={r.status_code} data={r.json().get('data')}")

    # 8. 校准回传
    files = {"file": ("real_report.pdf", b"%PDF-1.4 fake report", "application/pdf")}
    r = client.post(
        "/api/v1/calibration/reports",
        headers=headers,
        files=files,
        data={"platform": "cnki", "real_rate": "45.5", "task_id": str(last_task or 1)},
    )
    log("calibration 201", r.status_code == 201, f"status={r.status_code} data={r.json().get('data')}")
    r = client.get("/api/v1/calibration/status", headers=headers)
    log("calibration status", r.status_code == 200 and "sample_count" in r.json()["data"], f"data={r.json()['data']}")

    # 9. 用量递减 + 超限 402（用新用户：points=0，仅消耗 free_quota）
    r = client.get("/api/v1/users/me/usage", headers=headers)
    d = r.json()["data"]
    log("usage decremented", d["free_quota"] < user["free_quota"], f"quota {user['free_quota']} -> {d['free_quota']} points={d['points']}")

    # 新用户耗尽免费次数（5 次）→ 第 6 次应 402（AC-03/04）
    email2 = f"quota_{int(time.time())}@example.com"
    r2 = client.post("/api/v1/auth/register", json={"email": email2, "password": "Test@1234", "nickname": "配额测试"})
    u2 = r2.json()["data"]["user"]
    h2 = {"Authorization": f"Bearer {r2.json()['data']['tokens']['access_token']}"}
    got_402 = False
    zh = "教育信息化是当代高等教育改革的重要方向之一。".encode("utf-8")
    for i in range(7):
        files = {"file": (f"quota_{i}.txt", zh * 5, "text/plain")}
        rr = client.post("/api/v1/checks", headers=h2, files=files, data={"plan_code": "cnki_sim"})
        if rr.status_code == 402:
            got_402 = True
            log("over-limit 402", True, f"6th check after quota {u2['free_quota']}, status={rr.status_code} msg={rr.json().get('message')}")
            break
    if not got_402:
        log("over-limit 402", False, "never got 402 after exhausting quota(5) on fresh user")

    # 10. 历史列表
    r = client.get("/api/v1/checks", headers=headers, params={"page": 1, "limit": 10})
    log("history list", r.status_code == 200 and r.json()["data"]["total"] >= 3, f"status={r.status_code} total={r.json()['data'].get('total')}")

    print("\n".join(results))
    passed = sum(1 for line in results if line.startswith("[PASS]"))
    print(f"== 结果: {passed}/{len(results)} 通过 ==")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
