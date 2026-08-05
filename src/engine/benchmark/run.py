"""基准测试执行器：在标注测试集上计算 MAE/Spearman/Recall/Precision/p95。

用法：python -m engine.benchmark.run --testset testsets/labeled.jsonl --plan cnki_sim
"""

import argparse
import json
import os
import statistics
import time

from engine.corpus.build import DEFAULT_INDEX_DIR
from engine.pipeline import run_check

# 标注片段 label -> 引擎应命中的 highlight_type 映射
_LABEL_EXPECT = {"duplicate": {"high", "mid"}, "rewrite": {"mid", "cite"}}


def _spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman 秩相关系数（纯 Python 实现）。"""
    n = len(xs)
    if n < 2:
        return 0.0
    rank_x = _rank(xs)
    rank_y = _rank(ys)
    mean_x = sum(rank_x) / n
    mean_y = sum(rank_y) / n
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(rank_x, rank_y))
    var_x = sum((a - mean_x) ** 2 for a in rank_x)
    var_y = sum((b - mean_y) ** 2 for b in rank_y)
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov / (var_x * var_y) ** 0.5


def _rank(values: list[float]) -> list[float]:
    """平均秩。"""
    indexed = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1
    return ranks


def _overlap(seg_start: int, seg_end: int, label_start: int, label_end: int) -> bool:
    """区间重叠判定。

    以 min(片段长, 标注长) 为分母：重叠 >= 50% 的较短区间即视为命中。
    兼容"粗粒度整篇标注 + 细粒度引擎片段"的常见标注粒度差异。
    """
    inter = max(0, min(seg_end, label_end) - max(seg_start, label_start))
    seg_len = seg_end - seg_start
    label_len = max(1, label_end - label_start)
    denom = max(1, min(seg_len, label_len))
    return inter / denom >= 0.5


def _hit_segment(engine_segments: list[dict], label: dict) -> bool:
    expected = _LABEL_EXPECT.get(label.get("label", "duplicate"), set())
    for seg in engine_segments:
        if seg["highlight_type"] in expected and _overlap(
            seg["start_offset"], seg["end_offset"], label["start_offset"], label["end_offset"]
        ):
            return True
    return False


def run_benchmark(testset_path: str, plan: str = "cnki_sim", index_dir: str = DEFAULT_INDEX_DIR) -> dict:
    """在标注测试集上运行基准。"""
    with open(testset_path, "r", encoding="utf-8") as fh:
        lines = [json.loads(ln) for ln in fh if ln.strip()]
    true_rates: list[float] = []
    raw_scores: list[float] = []
    durations_ms: list[int] = []
    tp = fp = fn = 0
    samples: list[dict] = []

    plan_params = {
        "cnki_sim": {"platform": "cnki", "paper_type": "undergrad"},
        "vip_sim": {"platform": "vip", "paper_type": "undergrad"},
        "wanfang_sim": {"platform": "wanfang", "paper_type": "undergrad"},
    }.get(plan, {"platform": "cnki", "paper_type": "undergrad"})

    for item in lines:
        doc_path = item["doc_path"]
        with open(doc_path, "r", encoding="utf-8") as fh:
            text = fh.read()
        t0 = time.perf_counter()
        result = run_check(text, {**plan_params, "source_label": "语料库"}, index_dir=index_dir)
        durations_ms.append(int((time.perf_counter() - t0) * 1000))
        true_rates.append(float(item["true_rate"]))
        raw_scores.append(result.raw_score)

        # 片段评估（真值 segments）
        label_segments = item.get("segments", [])
        engine_segments = result.segments
        for label in label_segments:
            if _hit_segment(engine_segments, label):
                tp += 1
            else:
                fn += 1
        # FP：引擎标出但真值未标注的片段（近似：引擎片段与所有真值片段均不重叠）
        for seg in engine_segments:
            if not any(_overlap(seg["start_offset"], seg["end_offset"], lbl["start_offset"], lbl["end_offset"]) for lbl in label_segments):
                fp += 1

        samples.append(
            {
                "sample_id": item["sample_id"],
                "true_rate": item["true_rate"],
                "raw_score": result.raw_score,
                "duration_ms": result.duration_ms,
                "engine_segments": len(engine_segments),
            }
        )

    n = len(true_rates)
    mae = statistics.mean([abs(r - t) for r, t in zip(raw_scores, true_rates)]) if n else 0.0
    spearman = _spearman(raw_scores, true_rates) if n else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    p95 = _percentile(sorted(durations_ms), 0.95) if durations_ms else 0

    return {
        "plan_code": plan,
        "sample_count": n,
        "mae_raw": round(mae, 4),
        "spearman_raw": round(spearman, 4),
        "recall_dup": round(recall, 4),
        "precision_dup": round(precision, 4),
        "p95_ms": int(p95),
        "samples": samples,
    }


def _percentile(sorted_values: list[int], p: float) -> int:
    if not sorted_values:
        return 0
    idx = int((len(sorted_values) - 1) * p)
    return sorted_values[idx]


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="引擎基准测试")
    parser.add_argument("--testset", required=True)
    parser.add_argument("--plan", default="cnki_sim")
    parser.add_argument("--index-dir", default=DEFAULT_INDEX_DIR)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    report = run_benchmark(args.testset, args.plan, args.index_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":  # pragma: no cover
    main()
