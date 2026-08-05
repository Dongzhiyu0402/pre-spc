"""统一推理入口：-> (est_median, est_low, est_high, confidence)。

优先级：
1. 该桶线性模型已训练（样本 >= 30，AC-15）-> 线性预测
2. 冷启动规则 + 常数偏移兜底（Spec §11 已知坑）
"""

from engine.calibration.model_store import load_bucket_model, DEFAULT_MODEL_DIR
from engine.calibration.rules import predict_by_rules, CalibPrediction


def predict(
    raw_score: float,
    platform: str = "cnki",
    paper_type: str = "undergrad",
    sample_count: int = 0,
    model_dir: str = DEFAULT_MODEL_DIR,
) -> CalibPrediction:
    """统一推理。sample_count 用于冷启动区间收窄。"""
    bucket = load_bucket_model(model_dir, platform, paper_type)
    if bucket and bucket.get("kind") == "linear" and bucket.get("slope") is not None:
        slope = float(bucket["slope"])
        intercept = float(bucket["intercept"])
        residual_std = float(bucket.get("residual_std", 6.0))
        median = slope * raw_score + intercept
        half = 1.96 * residual_std
        confidence = _linear_confidence(bucket.get("sample_count", 0))
        return CalibPrediction(
            est_median=median,
            est_low=median - half,
            est_high=median + half,
            confidence=confidence,
            model_status="linear",
        )
    return predict_by_rules(raw_score, platform, sample_count)


def _linear_confidence(sample_count: int) -> float:
    """线性模型置信度：随样本增加收敛到 85。"""
    if sample_count >= 200:
        return 88.0
    if sample_count >= 100:
        return 82.0
    if sample_count >= 50:
        return 75.0
    return 65.0
