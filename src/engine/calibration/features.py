"""特征工程：raw_score/最长片段/命中统计/文档结构/平台 one-hot。

供校准规则与线性回归使用。纯函数，无副作用。
"""

from dataclasses import dataclass

from engine.scoring.segment_agg import SegmentAggResult


@dataclass
class CheckFeatures:
    """查重特征向量（字典形式便于存 JSONB）。"""

    raw_score: float
    max_run_len: int
    hit_ratio: float
    segment_count: int
    doc_length: int
    platform: str = "cnki"
    paper_type: str = "undergrad"

    def as_dict(self) -> dict:
        return {
            "raw_score": round(self.raw_score, 2),
            "max_run_len": self.max_run_len,
            "hit_ratio": round(self.hit_ratio, 4),
            "segment_count": self.segment_count,
            "doc_length": self.doc_length,
            "platform": self.platform,
            "paper_type": self.paper_type,
        }


def build_features(
    raw_score: float,
    max_run_len: int,
    segment_count: int,
    doc_length: int,
    platform: str = "cnki",
    paper_type: str = "undergrad",
) -> CheckFeatures:
    """构造特征。hit_ratio = max_run_len 相对文档长度的占比。"""
    hit_ratio = max_run_len / doc_length if doc_length > 0 else 0.0
    return CheckFeatures(
        raw_score=raw_score,
        max_run_len=max_run_len,
        hit_ratio=hit_ratio,
        segment_count=segment_count,
        doc_length=doc_length,
        platform=platform,
        paper_type=paper_type,
    )


def features_from_agg(agg: SegmentAggResult, doc_length: int, max_run_len: int, platform: str = "cnki", paper_type: str = "undergrad") -> CheckFeatures:
    """从聚合结果构造特征。"""
    return build_features(
        raw_score=agg.raw_score,
        max_run_len=max_run_len,
        segment_count=len(agg.segments),
        doc_length=doc_length,
        platform=platform,
        paper_type=paper_type,
    )
