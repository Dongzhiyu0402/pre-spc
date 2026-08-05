"""命中片段聚合 -> segments + sources + raw_score。

将 query 文本与候选集的命中片段聚合成报告片段：
- highlight_type: high（高重复红，长且相似度高）/ mid（中重复橙）/ cite（引用赭黄）
- matched_source: 来源标识（语料库/用户库/未知）
- raw_score: 命中字符数占比（0-100）
"""

from dataclasses import dataclass, field

from engine.recall.simhash_index import CorpusDoc
from engine.scoring.longest_match import longest_matched_runs


@dataclass
class AggSegment:
    """聚合后的命中片段。"""

    start_offset: int
    end_offset: int
    highlight_type: str
    matched_source: str
    similarity: float

    def to_dict(self) -> dict:
        return {
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "highlight_type": self.highlight_type,
            "matched_source": self.matched_source,
            "similarity": round(self.similarity, 2),
        }


@dataclass
class SegmentAggResult:
    """聚合结果。"""

    raw_score: float
    segments: list[AggSegment] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)


_HIGH_MIN_LEN = 20
_MID_MIN_LEN = 8
_CITE_MAX_SIM = 0.3  # 相似度较低的长片段按引用处理（占位规则）


def _classify(length: int, sim: float) -> str:
    if sim >= 0.6 and length >= _HIGH_MIN_LEN:
        return "high"
    if length >= _MID_MIN_LEN:
        return "mid"
    return "cite"


def _dedupe_runs(runs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """合并重叠/相邻 runs。"""
    if not runs:
        return []
    ordered = sorted(runs)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def aggregate_segments(query_text: str, candidates: list[CorpusDoc], source_label: str = "语料库") -> SegmentAggResult:
    """聚合候选命中片段。

    query_text 为清洗后的文本（含空格，偏移按该文本字符位置）。
    candidates 为候选文档（已含 ngram_grams）。
    """
    n = len(query_text)
    if n == 0:
        return SegmentAggResult(raw_score=0.0)

    # 合并所有候选的命中 runs
    all_runs: list[tuple[int, int]] = []
    for cand in candidates:
        runs = longest_matched_runs(query_text, cand.ngram_grams)
        all_runs.extend(runs)
    merged_runs = _dedupe_runs(all_runs)

    # 来源统计
    source_counter: dict[str, int] = {}
    for cand in candidates:
        source = source_label
        source_counter[source] = source_counter.get(source, 0) + 1

    # 计算命中字符数
    hit_chars = sum(end - start for start, end in merged_runs)
    raw_score = min(100.0, round(hit_chars / n * 100.0, 2))

    # 组装片段（每段相似度取该段内最大候选包含度近似：用长度占比）
    segments: list[AggSegment] = []
    for start, end in merged_runs:
        length = end - start
        # 相似度近似：片段长度占 query 比例映射，长片段更可能来自真实匹配
        sim = min(100.0, round(min(1.0, length / max(10, n)) * 100.0, 2))
        htype = _classify(length, sim)
        segments.append(
            AggSegment(
                start_offset=start,
                end_offset=end,
                highlight_type=htype,
                matched_source=source_label,
                similarity=sim,
            )
        )
    sources = [{"source": k, "count": v} for k, v in source_counter.items()]
    return SegmentAggResult(raw_score=raw_score, segments=segments, sources=sources)
