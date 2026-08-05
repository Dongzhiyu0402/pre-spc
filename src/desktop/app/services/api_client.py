"""后端 API 客户端（联网模式，JWT 复用 Web 同一账号体系）。

同步 httpx；baseURL 可配置（默认 http://localhost:8000/api/v1）。
响应信封 {code, data, message}；code != 0 抛 ApiClientError。
"""

import httpx

from app.config import DEFAULT_API_BASE


class ApiClientError(Exception):
    """API 业务错误（含后端 message）。"""

    def __init__(self, message: str, code: int = -1, status_code: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class ApiClient:
    """轻量后端客户端。"""

    def __init__(self, base_url: str = DEFAULT_API_BASE, access_token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    @staticmethod
    def _unwrap(resp: httpx.Response) -> dict:
        try:
            body = resp.json()
        except ValueError:
            raise ApiClientError("服务端返回异常", status_code=resp.status_code) from None
        if resp.status_code >= 400 or body.get("code", 0) != 0:
            raise ApiClientError(
                body.get("message", "请求失败"),
                code=body.get("code", -1),
                status_code=resp.status_code,
            )
        return body.get("data")

    def login(self, email: str, password: str) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=15) as client:
            resp = client.post("/auth/login", json={"email": email, "password": password})
            data = self._unwrap(resp)
        self.access_token = data["tokens"]["access_token"]
        return data

    def register(self, email: str, password: str, nickname: str) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=15) as client:
            resp = client.post("/auth/register", json={"email": email, "password": password, "nickname": nickname})
            data = self._unwrap(resp)
        self.access_token = data["tokens"]["access_token"]
        return data

    def list_plans(self) -> list[dict]:
        with httpx.Client(base_url=self.base_url, timeout=15, headers=self._headers()) as client:
            resp = client.get("/plans")
            return self._unwrap(resp)

    def create_check(self, file_path: str, plan_code: str) -> dict:
        with open(file_path, "rb") as fh:
            files = {"file": (file_path.split("/")[-1], fh)}
            with httpx.Client(base_url=self.base_url, timeout=120, headers=self._headers()) as client:
                resp = client.post("/checks", files=files, data={"plan_code": plan_code})
                return self._unwrap(resp)

    def get_check(self, task_id: int) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=15, headers=self._headers()) as client:
            resp = client.get(f"/checks/{task_id}")
            return self._unwrap(resp)

    def get_report(self, task_id: int) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=30, headers=self._headers()) as client:
            resp = client.get(f"/checks/{task_id}/report")
            return self._unwrap(resp)

    def list_checks(self, page: int = 1, limit: int = 20) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=15, headers=self._headers()) as client:
            resp = client.get("/checks", params={"page": page, "limit": limit})
            return self._unwrap(resp)

    def recheck(self, task_id: int, plan_code: str) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=15, headers=self._headers()) as client:
            resp = client.post(f"/checks/{task_id}/recheck", json={"plan_code": plan_code})
            return self._unwrap(resp)

    def submit_calibration(self, file_path: str, platform: str, real_rate: float, task_id: int) -> dict:
        with open(file_path, "rb") as fh:
            files = {"file": (file_path.split("/")[-1], fh)}
            data = {"platform": platform, "real_rate": str(real_rate), "task_id": str(task_id)}
            with httpx.Client(base_url=self.base_url, timeout=60, headers=self._headers()) as client:
                resp = client.post("/calibration/reports", files=files, data=data)
                return self._unwrap(resp)

    def get_usage(self) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=15, headers=self._headers()) as client:
            resp = client.get("/users/me/usage")
            return self._unwrap(resp)

    def get_calibration_status(self) -> dict:
        with httpx.Client(base_url=self.base_url, timeout=15, headers=self._headers()) as client:
            resp = client.get("/calibration/status")
            return self._unwrap(resp)
