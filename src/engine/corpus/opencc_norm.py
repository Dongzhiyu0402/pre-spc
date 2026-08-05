"""简繁归一。

优先使用 OpenCC（若已安装）；未安装时用内置常用简繁映射表兜底。
输出统一为简体。
"""

try:  # pragma: no cover
    from opencc import OpenCC  # type: ignore

    _CONVERTER = OpenCC("t2s")
except ImportError:  # pragma: no cover
    _CONVERTER = None

# 常用简繁映射（内置兜底子集，覆盖高频词）
_COMMON_T2S = {
    "為": "为",
    "與": "与",
    "於": "于",
    "這": "这",
    "個": "个",
    "對": "对",
    "從": "从",
    "來": "来",
    "學": "学",
    "術": "术",
    "論": "论",
    "文": "文",
    "研": "研",
    "究": "究",
    "報": "报",
    "告": "告",
    "檢": "检",
    "測": "测",
    "結": "结",
    "果": "果",
    "確": "确",
    "認": "认",
    "優": "优",
    "質": "质",
    "量": "量",
    "數": "数",
    "據": "据",
    "經": "经",
    "驗": "验",
    "證": "证",
    "實": "实",
    "驗": "验",
}


def to_simplified(text: str) -> str:
    """繁体 -> 简体。OpenCC 可用时优先，否则内置映射。"""
    if not text:
        return text
    if _CONVERTER is not None:  # pragma: no cover
        return _CONVERTER.convert(text)
    return "".join(_COMMON_T2S.get(ch, ch) for ch in text)
