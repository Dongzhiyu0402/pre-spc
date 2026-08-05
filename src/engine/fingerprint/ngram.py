"""字符级 n-gram 指纹（2-6 字多窗口，主判据）。

对齐知网"连续字符匹配"信号：免分词误差，支持片段高亮。
"""

from collections import Counter
from typing import Iterable

DEFAULT_WINDOWS = (2, 3, 4, 5, 6)


def iter_ngrams(text: str, n: int) -> Iterable[str]:
    """按字符窗口滑动，生成 n-gram 子串。"""
    if n <= 0:
        return
    for i in range(len(text) - n + 1):
        yield text[i : i + n]


def ngram_counter(text: str, windows: tuple[int, ...] = DEFAULT_WINDOWS) -> Counter:
    """多窗口 n-gram 计数（聚合）。"""
    counter: Counter = Counter()
    for n in windows:
        for gram in iter_ngrams(text, n):
            counter[gram] += 1
    return counter


def ngram_set(text: str, windows: tuple[int, ...] = DEFAULT_WINDOWS) -> set[str]:
    """多窗口 n-gram 集合（去重，用于包含度）。"""
    grams: set[str] = set()
    for n in windows:
        grams.update(iter_ngrams(text, n))
    return grams


def containment_score(query_grams: set[str], doc_grams: set[str]) -> float:
    """n-gram 包含度：query 中有多少比例出现在 doc 中。

    返回 0-1 的分数。多窗口已聚合，长度加权在调用方处理。
    """
    if not query_grams:
        return 0.0
    return len(query_grams & doc_grams) / len(query_grams)
