"""本地离线查重服务：调 engine.run_check（AC-16 原文不出本机）。

文档解析复用 engine 的 doc_extractor + clean_text，与后端完全一致。
"""

import time
from pathlib import Path

from app.config import MAX_UPLOAD_MB, MAX_WORD_COUNT

ALLOWED_EXT = {".txt", ".md", ".docx", ".pdf"}

DISCLAIMER = "预估仅供参考，非官方检测报告"


class CheckError(Exception):
    """离线查重错误。"""


def _count_chinese(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def extract_document(file_path: str) -> str:
    """抽取并校验文档 -> 原始文本。校验失败抛 CheckError（不消耗次数）。"""
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXT:
        raise CheckError(f"不支持的文件类型: {ext or '未知'}，仅支持 txt/md/docx/pdf")
    size = path.stat().st_size
    if size > MAX_UPLOAD_MB * 1024 * 1024:
        raise CheckError(f"文件超过 {MAX_UPLOAD_MB}MB 限制")
    from engine.cleaning.doc_extractor import extract_text_from_bytes

    data = path.read_bytes()
    try:
        raw = extract_text_from_bytes(data, path.name)
    except Exception as exc:
        raise CheckError(f"文档解析失败: {exc}") from exc
    from engine.cleaning.text_cleaner import clean_text

    word_count = _count_chinese(clean_text(raw))
    if word_count == 0:
        raise CheckError("文件内容为空，无法查重")
    if word_count > MAX_WORD_COUNT:
        raise CheckError(f"文件超过 {MAX_WORD_COUNT} 字上限")
    return raw


def run_local_check(file_path: str, plan_code: str = "cnki_sim") -> dict:
    """本地引擎查重，返回后端报告同构结构。"""
    raw = extract_document(file_path)
    plan_params = {
        "cnki_sim": {"platform": "cnki", "paper_type": "undergrad"},
        "vip_sim": {"platform": "vip", "paper_type": "undergrad"},
        "wanfang_sim": {"platform": "wanfang", "paper_type": "undergrad"},
    }.get(plan_code, {"platform": "cnki", "paper_type": "undergrad"})

    from engine.pipeline import run_check

    t0 = time.perf_counter()
    result = run_check(raw, {**plan_params, "source_label": "语料库"})
    duration_ms = int((time.perf_counter() - t0) * 1000)

    pred = result.prediction
    return {
        "task_id": 0,
        "plan_code": plan_code,
        "est_median": float(pred.get("est_median", 0)),
        "est_low": float(pred.get("est_low", 0)),
        "est_high": float(pred.get("est_high", 0)),
        "confidence": float(pred.get("confidence", 0)),
        "segments": result.segments,
        "sources": result.sources,
        "raw_score": result.raw_score,
        "file_name": Path(file_path).name,
        "file_path": str(Path(file_path).resolve()),
        "duration_ms": duration_ms,
        "disclaimer": DISCLAIMER,
        "model_status": pred.get("model_status", "cold_start"),
    }
