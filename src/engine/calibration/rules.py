"""冷启动规则 + 常数偏移（校准样本不足时兜底）。

规则思路（与"知网级语料库不可获取"的坑对应）：
- raw_score 已反映 n-gram 包含度，但新闻/百科语料对学术论文存在系统性偏低/偏高偏差。
- 冷启动阶段用平台常数偏移 + 分段规则映射出预估区间，并给出低置信度提示。
"""

from dataclasses import dataclass

# 平台常数偏移（冷启动默认，样本积累后由线性回归替代）
_PLATFORM_OFFSET = {
    "cnki": 3.0,
    "vip": 1.5,
    "wanfang": 0.5,
}

# 置信度（冷启动阶段固定较低）
_COLD_CONFIDENCE = 35.0


@dataclass
class CalibPrediction:
    """校准预测输出。"""

    est_median: float
    est_low: float
    est_high: float
    confidence: float
    model_status: str

    def as_dict(self) -> dict:
        return {
            "est_median": round(self.est_median, 2),
            "est_low": round(self.est_low, 2),
            "est_high": round(self.est_high, 2),
            "confidence": round(self.confidence, 2),
            "model_status": self.model_status,
        }


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def predict_by_rules(raw_score: float, platform: str = "cnki", sample_count: int = 0) -> CalibPrediction:
    """冷启动规则预测。

    偏移后中值 = raw_score + 平台偏移（随样本数微调）。
    区间宽度随样本数收窄（0 样本最宽，接近 30 时收窄）。
    """
    offset = _PLATFORM_OFFSET.get(platform, 1.0)
    median = _clamp(raw_score + offset)
    # 样本越多区间越窄；冷启动最宽 ±12
    half_width = max(4.0, 12.0 - sample_count * 0.25)
    low = _clamp(median - half_width)
    high = _clamp(median + half_width)
    confidence = _clamp(_COLD_CONFIDENCE + sample_count * 1.5, 35.0, 60.0)
    return CalibPrediction(
        est_median=median,
        est_low=low,
        est_high=high,
        confidence=confidence,
        model_status="cold_start",
    )
