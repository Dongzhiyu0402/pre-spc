"""MinHash 签名（语料库建库/去重）。

无第三方依赖的轻量实现：对文本做 shingle（字符 n-gram）集合，
用 k 个确定性哈希取最小值生成签名。用于语料去重与相似文档快速判等。
"""

from engine.fingerprint.ngram import iter_ngrams
from engine.fingerprint.simhash import _hash64

DEFAULT_NUM_PERM = 64
DEFAULT_SHINGLE = 5


def _minhash_signature(shingles: set[str], num_perm: int) -> list[int]:
    """对 shingle 集合生成 num_perm 维 MinHash 签名。

    每个哈希函数取 shingle 哈希的最小值。确定性。
    """
    sig = [0xFFFFFFFFFFFFFFFF] * num_perm
    for shingle in shingles:
        h = _hash64(shingle)
        for k in range(num_perm):
            # 不同哈希函数：h ^ (k * salt) 近似独立
            hk = (h ^ ((k + 1) * 0x9E3779B97F4A7C15)) & 0xFFFFFFFFFFFFFFFF
            if hk < sig[k]:
                sig[k] = hk
    return sig


def minhash_signature(text: str, num_perm: int = DEFAULT_NUM_PERM, shingle: int = DEFAULT_SHINGLE) -> list[int]:
    """文本 -> MinHash 签名。"""
    shingles = set(iter_ngrams(text, shingle))
    if not shingles:
        return [0] * num_perm
    return _minhash_signature(shingles, num_perm)


def jaccard_estimate(sig_a: list[int], sig_b: list[int]) -> float:
    """由签名估计 Jaccard 相似度（0-1）。"""
    if not sig_a or len(sig_a) != len(sig_b):
        return 0.0
    equal = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
    return equal / len(sig_a)
