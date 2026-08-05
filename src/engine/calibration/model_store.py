"""模型存储：按 platform+paper_type 分桶读写模型文件。

存储目录：engine/models/calibration/{platform}_{paper_type}.json
纯 JSON，无 pickle，避免版本/安全风险。
"""

import json
import os

DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "calibration")


def _bucket_filename(platform: str, paper_type: str) -> str:
    return f"{platform}_{paper_type}.json"


def _bucket_path(model_dir: str, platform: str, paper_type: str) -> str:
    return os.path.join(model_dir, _bucket_filename(platform, paper_type))


def load_bucket_model(model_dir: str, platform: str, paper_type: str) -> dict | None:
    """加载某桶模型。不存在返回 None。"""
    path = _bucket_path(model_dir, platform, paper_type)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_bucket_model(model_dir: str, platform: str, paper_type: str, payload: dict) -> str:
    """保存某桶模型，返回写入路径。"""
    os.makedirs(model_dir, exist_ok=True)
    path = _bucket_path(model_dir, platform, paper_type)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return path


def list_buckets(model_dir: str) -> list[str]:
    """列出已训练桶（文件名，去扩展名）。"""
    if not os.path.isdir(model_dir):
        return []
    return [f[:-5] for f in os.listdir(model_dir) if f.endswith(".json")]
