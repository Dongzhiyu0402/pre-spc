"""基准指标计算测试（engine-benchmark §3 要求：指标必须写进测试用例）。

验证 MAE/Spearman/Recall 计算在已知小样本上的正确性，禁止"肉眼比对"。
"""

import json

from engine.benchmark.run import _rank, _spearman, _overlap, _hit_segment, run_benchmark
from engine.benchmark.gate import evaluate


def test_spearman_perfect_monotonic():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 4.0, 6.0, 8.0, 10.0]
    assert _spearman(xs, ys) == 1.0


def test_spearman_reverse():
    xs = [1.0, 2.0, 3.0]
    ys = [3.0, 2.0, 1.0]
    assert _spearman(xs, ys) == -1.0


def test_spearman_ties():
    ranks = _rank([1.0, 1.0, 2.0])
    assert ranks == [1.5, 1.5, 3.0]


def test_overlap_min_denominator():
    # 引擎小片段 vs 粗粒度大标注：按较短区间判定
    assert _overlap(20, 37, 0, 409) is True
    # 完全不相交
    assert _overlap(100, 200, 0, 50) is False


def test_hit_segment_types():
    segs = [
        {"start_offset": 10, "end_offset": 30, "highlight_type": "high", "matched_source": "语料库", "similarity": 90.0},
        {"start_offset": 100, "end_offset": 120, "highlight_type": "mid", "matched_source": "语料库", "similarity": 50.0},
    ]
    dup_label = {"start_offset": 15, "end_offset": 25, "label": "duplicate"}
    rewrite_label = {"start_offset": 105, "end_offset": 115, "label": "rewrite"}
    assert _hit_segment(segs, dup_label) is True
    assert _hit_segment(segs, rewrite_label) is True


def test_gate_evaluate():
    report = {"mae_raw": 7.0, "spearman_raw": 0.9, "recall_dup": 0.8, "p95_ms": 100}
    passed, failures = evaluate(report, mae_max=15, spearman_min=0.6, recall_min=0.7, p95_max=30000)
    assert passed and not failures
    bad = {"mae_raw": 30.0, "spearman_raw": 0.9, "recall_dup": 0.8, "p95_ms": 100}
    passed, failures = evaluate(bad, mae_max=15, spearman_min=0.6, recall_min=0.7, p95_max=30000)
    assert not passed and any("MAE" in f for f in failures)


def test_benchmark_runs_on_demo(tmp_path):
    """端到端：在小型标注集上跑基准，指标为数值且在合法范围。"""
    import os

    testset = tmp_path / "labeled.jsonl"
    docs = tmp_path / "docs"
    docs.mkdir()
    corpus_text = "随着信息技术的快速发展教育信息化成为高等教育改革的重要方向之一。"
    (docs / "a_001.txt").write_text(corpus_text * 2, encoding="utf-8")
    (docs / "c_001.txt").write_text("完全原创的新内容不来自任何已有资料。", encoding="utf-8")
    lines = [
        json.dumps({"sample_id": "A-001", "doc_path": str(docs / "a_001.txt"), "true_rate": 90.0, "segments": [{"start_offset": 0, "end_offset": len(corpus_text * 2), "label": "duplicate"}]}, ensure_ascii=False),
        json.dumps({"sample_id": "C-001", "doc_path": str(docs / "c_001.txt"), "true_rate": 5.0, "segments": []}, ensure_ascii=False),
    ]
    testset.write_text("\n".join(lines), encoding="utf-8")
    report = run_benchmark(str(testset), "cnki_sim")
    assert report["sample_count"] == 2
    assert 0 <= report["mae_raw"] <= 100
    assert -1 <= report["spearman_raw"] <= 1
    assert 0 <= report["recall_dup"] <= 1
    assert report["p95_ms"] >= 0
