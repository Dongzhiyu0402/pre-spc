"""引擎流水线端到端测试（含内置 demo 语料）。"""

from engine.pipeline import run_check
from engine.corpus.build import build_default_corpus
from engine.cleaning.doc_extractor import extract_text_from_bytes


def test_run_check_empty_text():
    result = run_check("", {})
    assert result.raw_score == 0.0
    assert result.prediction["est_median"] >= 0


def test_run_check_deterministic():
    text = "随着信息技术的快速发展教育信息化成为高等教育改革的重要方向之一。"
    r1 = run_check(text, {"platform": "cnki"})
    r2 = run_check(text, {"platform": "cnki"})
    assert r1.raw_score == r2.raw_score
    assert r1.segments == r2.segments


def test_run_check_repeated_text_scores_higher():
    # 与 demo 语料几乎完全重复的文本应得高分
    demo_index = build_default_corpus()
    assert demo_index.size() > 0
    repeated = "随着信息技术的快速发展，教育信息化已经成为当代高等教育改革的重要方向之一。"
    r = run_check(repeated, {"platform": "cnki"})
    assert r.raw_score > 5


def test_run_check_original_scores_low():
    original = "完全原创的全新内容，不来自任何已有资料，属于作者独立构思的新观点。"
    r = run_check(original, {"platform": "cnki"})
    assert r.raw_score < 40


def test_run_check_metrics_and_chapters():
    """报告扩展字段：metrics/chapters 在 pipeline 输出且结构正确。"""
    repeated = "随着信息技术的快速发展，教育信息化已经成为当代高等教育改革的重要方向之一。"
    r = run_check(repeated, {"platform": "cnki"})
    # metrics 三键齐全，口径：无本人标记数据时 exclude_self_rate 为 None
    assert set(r.metrics.keys()) == {"exclude_cite_rate", "exclude_self_rate", "max_single_source_rate"}
    assert r.metrics["exclude_self_rate"] is None
    assert r.metrics["exclude_cite_rate"] >= 0
    assert r.metrics["max_single_source_rate"] >= 0
    # chapters：无章节结构给单一 "全文" 条目
    assert isinstance(r.chapters, list) and len(r.chapters) >= 1
    assert "title" in r.chapters[0] and "rate" in r.chapters[0]
    assert 0 <= r.chapters[0]["rate"] <= 100


def test_doc_extractor_txt():
    text = extract_text_from_bytes("你好世界".encode("utf-8"), "a.txt")
    assert text == "你好世界"


def test_doc_extractor_unsupported():
    import pytest

    with pytest.raises(Exception):
        extract_text_from_bytes(b"data", "a.exe")
