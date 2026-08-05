"""认证端点测试：注册/登录/刷新/当前用户（AC-12）。"""


async def test_register_success(client, auth_headers_factory):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "reg@example.com", "password": "Test@1234", "nickname": "newbie"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["user"]["email"] == "reg@example.com"
    assert data["user"]["free_quota"] >= 5  # AC-12 注册送次数
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


async def test_register_duplicate_conflict(client):
    payload = {"email": "dup@example.com", "password": "Test@1234", "nickname": "dup"}
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201
    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["code"] != 0


async def test_register_weak_password_422(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "123", "nickname": "weak"},
    )
    assert resp.status_code == 422


async def test_login_success_and_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "Test@1234", "nickname": "login"},
    )
    ok = await client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "Test@1234"}
    )
    assert ok.status_code == 200
    bad = await client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "wrongpass"}
    )
    assert bad.status_code == 401


async def test_refresh_token(client, auth_headers_factory):
    _, tokens, _, _ = await auth_headers_factory(client, email="rf@example.com")
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    resp2 = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert resp2.status_code == 401
