"""报告/校准/用量模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SegmentOut(BaseModel):
    start_offset: int
    end_offset: int
    highlight_type: Literal["high", "mid", "cite"]
    matched_source: str
    similarity: float
    source_detail: list["SourceDetailOut"] = Field(default_factory=list)


class SourceDetailOut(BaseModel):
    """来源明细（可从引擎 sources 组装，缺字段置 null）。"""

    title: str | None = None
    author: str | None = None
    source: str | None = None
    similarity: float | None = None
    is_cited: bool | None = None
    year: int | None = None


class MetricsOut(BaseModel):
    """三指标卡：去除引用率 / 去除本人率 / 单篇最大复制比。"""

    exclude_cite_rate: float | None = None
    exclude_self_rate: float | None = None
    max_single_source_rate: float | None = None


class ChapterOut(BaseModel):
    title: str
    rate: float


class SourceOut(BaseModel):
    source: str
    count: int


DISCLAIMER = "预估仅供参考，非官方检测报告"


class ReportOut(BaseModel):
    task_id: int
    plan_code: str
    est_median: float
    est_low: float
    est_high: float
    confidence: float
    segments: list[SegmentOut]
    sources: list[SourceOut]
    full_text: str = ""
    metrics: MetricsOut | None = None
    chapters: list[ChapterOut] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER
    created_at: datetime | None = None


class CalibrationStatusOut(BaseModel):
    sample_count: int
    model_version: str | None
    mae: float | None
    model_status: str = "cold_start"


class SampleSubmitted(BaseModel):
    sample_id: int
    status: str = "pending_validation"


class UsageOut(BaseModel):
    free_quota: int
    points: int
