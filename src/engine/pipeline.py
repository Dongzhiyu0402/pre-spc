"""引擎主流水线：run_check(text, plan_params) -> EngineResult。

流程：清洗 -> SimHash 召回 -> n-gram 包含度精算 -> 片段聚合 -> 校准预测。
片段偏移映射回原文坐标（报告全文高亮 AC-05 使用原文偏移）。
确定性：同输入同输出（无随机）。
"""

import time
from dataclasses import dataclass, field

from engine.cleaning.text_cleaner import clean_text_with_map, map_segments_to_raw
from engine.corpus.build import load_or_build_index, DEFAULT_INDEX_DIR
from engine.fingerprint.simhash import simhash
from engine.fingerprint.ngram import ngram_set
from engine.scoring.segment_agg import aggregate_segments, SegmentAggResult
from engine.scoring.longest_match import longest_match_length
from engine.scoring.containment import candidate_containment
from engine.scoring.metrics import compute_metrics, compute_chapters
from engine.calibration.features import features_from_agg, CheckFeatures
from engine.calibration.predict import predict
from engine.calibration.rules import CalibPrediction
from engine.calibration.model_store import DEFAULT_MODEL_DIR

ENGINE_VERSION = "0.1.0"

# 候选保留阈值：任何包含度 > 0 的候选都参与片段聚合（防漏检）
_CANDIDATE_MIN_SCORE = 0.01


@dataclass
class EngineResult:
    """引擎输出（与 Web/桌面解耦）。"""

    raw_score: float
    segments: list[dict] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    chapters: list[dict] = field(default_factory=list)
    features: dict = field(default_factory=dict)
    prediction: dict = field(default_factory=dict)
    engine_version: str = ENGINE_VERSION
    corpus_doc_count: int = 0
    duration_ms: int = 0

    def as_dict(self) -> dict:
        return {
            "raw_score": round(self.raw_score, 2),
            "segments": self.segments,
            "sources": self.sources,
            "metrics": self.metrics,
            "chapters": self.chapters,
            "features": self.features,
            "prediction": self.prediction,
            "engine_version": self.engine_version,
            "corpus_doc_count": self.corpus_doc_count,
            "duration_ms": self.duration_ms,
        }


def _count_chinese_chars(text: str) -> int:
    return sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")


def run_check(
    text: str,
    plan_params: dict | None = None,
    index_dir: str = DEFAULT_INDEX_DIR,
) -> EngineResult:
    """统一入口。

    plan_params 支持字段：
    - platform: 平台标识（cnki/vip/wanfang），用于校准分桶，默认 cnki
    - paper_type: 论文类型（undergrad/postgrad/journal），默认 undergrad
    - source_label: 来源提示文案，默认 "语料库"
    - sample_count: 该校准桶已积累样本数（冷启动区间收窄），默认 0
    """
    start = time.perf_counter()
    params = plan_params or {}
    platform = params.get("platform", "cnki")
    paper_type = params.get("paper_type", "undergrad")
    source_label = params.get("source_label", "语料库")
    sample_count = int(params.get("sample_count", 0))

    cleaned, forward_map = clean_text_with_map(text)
    doc_length = _count_chinese_chars(cleaned)

    index = load_or_build_index(index_dir)

    # 空文本直接返回 0
    if doc_length == 0 or not cleaned.strip():
        pred = predict(0.0, platform, paper_type, sample_count, model_dir=DEFAULT_MODEL_DIR)
        result = EngineResult(
            raw_score=0.0,
            prediction=pred.as_dict(),
            corpus_doc_count=index.size(),
            duration_ms=int((time.perf_counter() - start) * 1000),
        )
        return result

    # 1) SimHash 召回
    fp = simhash(cleaned)
    query_grams = ngram_set(cleaned)
    candidates = index.recall(fp, top_k=20, max_distance=24, query_grams=query_grams)

    # 2) n-gram 精算（排序候选，保留分数用于来源统计）
    scored = candidate_containment(cleaned, candidates)
    candidates = [cand for cand, _ in scored if _ >= _CANDIDATE_MIN_SCORE]

    # 3) 片段聚合（清洗文本坐标）
    agg: SegmentAggResult = aggregate_segments(cleaned, candidates, source_label=source_label)
    max_run_len = max((longest_match_length(cleaned, cand.ngram_grams) for cand in candidates), default=0)

    # 4) 特征 + 校准预测
    features: CheckFeatures = features_from_agg(agg, doc_length, max_run_len, platform, paper_type)
    pred: CalibPrediction = predict(agg.raw_score, platform, paper_type, sample_count, model_dir=DEFAULT_MODEL_DIR)

    # 5) 片段偏移映射回原文坐标
    raw_segments = map_segments_to_raw([s.to_dict() for s in agg.segments], forward_map)

    # 6) 报告指标与章节聚合（metrics/chapters）
    doc_raw_len = len(text)
    metrics = compute_metrics(raw_segments, doc_raw_len)
    chapters = compute_chapters(text, raw_segments)

    result = EngineResult(
        raw_score=agg.raw_score,
        segments=raw_segments,
        sources=agg.sources,
        metrics=metrics,
        chapters=chapters,
        features=features.as_dict(),
        prediction=pred.as_dict(),
        corpus_doc_count=index.size(),
        duration_ms=int((time.perf_counter() - start) * 1000),
    )
    return result
