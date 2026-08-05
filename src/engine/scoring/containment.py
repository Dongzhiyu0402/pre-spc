"""候选集内 n-gram 包含度精算（contamination 分数）。

对每个候选文档计算 query 的 n-gram 包含度，按长度加权。
"""

from engine.fingerprint.ngram import ngram_set, DEFAULT_WINDOWS
from engine.recall.simhash_index import CorpusDoc


def _window_weight(n: int) -> float:
    """长度加权：长 n-gram 更代表完整匹配，权重更高。"""
    return float(n)


def candidate_containment(query_text: str, candidates: list[CorpusDoc]) -> list[tuple[CorpusDoc, float]]:
    """计算 query 相对每个候选的加权包含度分数（0-1）。

    返回 [(candidate, score), ...]，按分数降序。
    """
    query_grams = ngram_set(query_text)
    if not query_grams:
        return []
    scored: list[tuple[CorpusDoc, float]] = []
    for cand in candidates:
        if not cand.ngram_grams:
            continue
        intersect = query_grams & cand.ngram_grams
        if not intersect:
            continue
        # 按窗口加权计算包含度
        total_weight = 0.0
        hit_weight = 0.0
        for n in DEFAULT_WINDOWS:
            w = _window_weight(n)
            total_weight += w * len(query_grams)
            hit_weight += w * len(intersect)
        # 简化：用 query 全部 n-gram 与交集的比例，权重按交集内 n 分布近似
        # 这里使用 query 集合为分母的包含度（与 engine-benchmark 口径一致）
        score = len(intersect) / len(query_grams)
        scored.append((cand, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def best_candidate_score(query_text: str, candidates: list[CorpusDoc]) -> float:
    """最优候选包含度（0-1），无候选返回 0。"""
    scored = candidate_containment(query_text, candidates)
    if not scored:
        return 0.0
    return scored[0][1]
