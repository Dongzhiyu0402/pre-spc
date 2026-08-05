"""GBDT 校准（样本 >= 200 时的增强路径）。

MVP 阶段以线性回归为主（Spec：50-200 线性，>=200 LightGBM）。
本模块预留接口；未安装 lightgbm 时回退到线性回归，避免硬依赖。
"""

from engine.calibration.linear import LinearModel, train_linear_model


def train_gbdt_model(samples: list[tuple[float, float]]) -> LinearModel:
    """GBDT 训练接口（占位）。

    当前无 lightgbm 依赖，直接回退线性回归。未来接入 lightgbm 时替换实现，
    保持 predict 接口不变。
    """
    return train_linear_model(samples)


def is_gbdt_available() -> bool:
    try:
        import lightgbm  # noqa: F401

        return True
    except ImportError:
        return False
