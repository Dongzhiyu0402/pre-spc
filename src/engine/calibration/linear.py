"""线性回归校准（样本 50-200）。

纯 Python 最小二乘实现（无 numpy/sklearn 依赖），
对 y = a * raw_score + b 拟合，MAE 评估，区间由残差分布给出。
确定性：同输入同输出。
"""

from dataclasses import dataclass, field


@dataclass
class LinearModel:
    """一元线性回归模型。"""

    slope: float = 1.0
    intercept: float = 0.0
    sample_count: int = 0
    mae: float = 0.0
    residual_std: float = 6.0

    def to_dict(self) -> dict:
        return {
            "kind": "linear",
            "slope": round(self.slope, 6),
            "intercept": round(self.intercept, 6),
            "sample_count": self.sample_count,
            "mae": round(self.mae, 4),
            "residual_std": round(self.residual_std, 4),
        }


def _fit_linear(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """最小二乘拟合 y = a*x + b。返回 (a, b)。"""
    n = len(xs)
    if n == 0:
        return 1.0, 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0:
        return 0.0, mean_y
    slope = num / den
    intercept = mean_y - slope * mean_x
    return slope, intercept


def train_linear_model(samples: list[tuple[float, float]]) -> LinearModel:
    """训练一元线性模型。samples = [(raw_score, real_rate), ...]。"""
    if len(samples) < 2:
        return LinearModel()
    xs = [s[0] for s in samples]
    ys = [s[1] for s in samples]
    slope, intercept = _fit_linear(xs, ys)
    preds = [slope * x + intercept for x in xs]
    errors = [abs(p - y) for p, y in zip(preds, ys)]
    mae = sum(errors) / len(errors)
    # 残差标准差（ddof=1），用于区间
    mean_err = sum(errors) / len(errors)
    var = sum((e - mean_err) ** 2 for e in errors) / max(1, len(errors) - 1)
    residual_std = var ** 0.5
    return LinearModel(
        slope=slope,
        intercept=intercept,
        sample_count=len(samples),
        mae=mae,
        residual_std=residual_std,
    )


def predict_linear(model: LinearModel, raw_score: float) -> tuple[float, float, float]:
    """预测 (median, low, high)，区间 = median ± 1.96 * residual_std。"""
    median = model.slope * raw_score + model.intercept
    half = 1.96 * model.residual_std
    return median, median - half, median + half
