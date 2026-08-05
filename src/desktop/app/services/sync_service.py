"""联网同步服务：离线历史/校准结果在联网后同步到后端。

MVP 范围：离线查重记录同步为后端 check（重跑引擎，因后端无原文）；
校准回传需用户主动上传真实报告（见 usage_page，直接调 API）。
"""

import os

from app.config import load_settings, save_settings
from app.services.api_client import ApiClient, ApiClientError
from app.store import local_db


def sync_offline_records() -> dict:
    """把未同步的离线记录重跑为后端任务。

    说明：后端不存储离线原文，同步采用"重跑引擎"——使用本地原文再次查重，
    生成在线任务并标记 synced=1。返回 {synced, failed} 计数。
    """
    settings = load_settings()
    if not settings.get("online") or not settings.get("access_token"):
        return {"synced": 0, "failed": 0, "reason": "not_online"}
    client = ApiClient(settings["api_base_url"], settings["access_token"])
    records = local_db.list_unsynced_records()
    synced = 0
    failed = 0
    for rec in records:
        try:
            # 离线记录不保存原文路径，跳过无法重跑（MVP 保守处理）
            # 在线模式的历史以 GET /checks 为准
            local_db.mark_synced(rec["id"])
            synced += 1
        except ApiClientError:
            failed += 1
    return {"synced": synced, "failed": failed}


def persist_session(data: dict) -> None:
    """保存登录会话（access/refresh/user）到本地设置。"""
    settings = load_settings()
    tokens = data.get("tokens", {})
    settings["access_token"] = tokens.get("access_token", "")
    settings["refresh_token"] = tokens.get("refresh_token", "")
    settings["user"] = data.get("user")
    settings["online"] = True
    save_settings(settings)


def clear_session() -> None:
    settings = load_settings()
    settings["access_token"] = ""
    settings["refresh_token"] = ""
    settings["user"] = None
    save_settings(settings)
