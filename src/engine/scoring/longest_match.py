"""最长连续命中片段统计（对齐知网"连续字符匹配"信号）。

对 query 每个字符位置，判断以该位置起头的 2-gram 是否在候选 n-gram 集合中，
得到布尔匹配数组，再聚合为连续 run，过滤短 run，输出 (start, end) 字符偏移。
"""

from engine.fingerprint.ngram import iter_ngrams


def matched_positions(query_text: str, cand_grams: set[str]) -> list[bool]:
    """每个字符位置是否命中（2-gram 起点命中）。"""
    n = len(query_text)
    hits = [False] * n
    if n < 2:
        return hits
    for i in range(n - 1):
        gram = query_text[i : i + 2]
        if gram in cand_grams:
            hits[i] = True
    return hits


def longest_matched_runs(query_text: str, cand_grams: set[str], min_run: int = 8) -> list[tuple[int, int]]:
    """最长连续命中片段（合并相邻，过滤 < min_run 的短片段）。

    返回 [(start, end), ...]，end 为开区间。确定性。
    """
    hits = matched_positions(query_text, cand_grams)
    n = len(query_text)
    runs: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if hits[i]:
            j = i
            while j < n and hits[j]:
                j += 1
            # 命中的起点位置 i..j-1，实际覆盖字符 i..j+1（因为 2-gram 覆盖 2 字符）
            runs.append((i, min(j + 1, n)))
            i = j
        else:
            i += 1
    merged: list[tuple[int, int]] = []
    for start, end in runs:
        if end - start >= min_run:
            merged.append((start, end))
    return merged


def longest_match_length(query_text: str, cand_grams: set[str]) -> int:
    """最长连续命中片段长度（字符数）。"""
    runs = longest_matched_runs(query_text, cand_grams, min_run=1)
    if not runs:
        return 0
    return max(end - start for start, end in runs)
