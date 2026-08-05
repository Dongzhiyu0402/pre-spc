"""桌面端本地配置：服务端地址、离线/在线模式、存储路径。"""

import json
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = APP_DIR / "resources"

DEFAULT_API_BASE = "http://localhost:8000/api/v1"

# 本地数据目录（用户目录下，避免打包后不可写）
LOCAL_DATA_DIR = Path(os.environ.get("PRE_DESKTOP_DATA", Path.home() / ".pre-spc"))

DB_PATH = LOCAL_DATA_DIR / "local.db"
SETTINGS_PATH = LOCAL_DATA_DIR / "settings.json"

# 上传限制（对齐 Spec §10）
MAX_UPLOAD_MB = 50
MAX_WORD_COUNT = 100000

# 平台显示名（方案 code -> 中文名，供离线模式固定方案）
PLAN_LABELS = {
    "cnki_sim": "知网模拟",
    "vip_sim": "维普模拟",
    "wanfang_sim": "万方模拟",
    "api_placeholder": "第三方 API",
}

DEFAULT_PLAN_CODES = ["cnki_sim", "vip_sim", "wanfang_sim"]


def _default_settings() -> dict:
    return {
        "api_base_url": DEFAULT_API_BASE,
        "online": False,
        "threshold": 20,
        "access_token": "",
        "refresh_token": "",
        "user": None,
    }


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    merged = _default_settings()
    merged.update(data)
    return merged


def save_settings(settings: dict) -> None:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, ensure_ascii=False, indent=2)
