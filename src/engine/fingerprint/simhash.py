"""SimHash 64 位指纹（候选召回）。

实现：对文本按空格/标点切词（fallback 为字符块），每个 token 计算 64 位哈希，
按位加权累加得到 64 维向量，再量化为 64 位指纹。
确定性：同输入同输出。
"""

import re

_BIT_MASK = (1 << 64) - 1


def _hash64(data: str) -> int:
    """FNV-1a 64 位哈希，确定性。"""
    h = 0xCBF29CE484222325
    for ch in data:
        h ^= ord(ch)
        h = (h * 0x100000001B3) & _BIT_MASK
    return h


def _tokenize(text: str) -> list[str]:
    """粗粒度切词：连续中文串/连续字母数字串为一个 token。"""
    return re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]{2,}|[A-Za-z0-9]+", text)


def simhash(text: str, hash_size: int = 64) -> int:
    """计算文本 SimHash 指纹（64 位 int）。"""
    if not text:
        return 0
    vector = [0] * hash_size
    tokens = _tokenize(text)
    if not tokens:
        # 极短文本退化为字符块
        tokens = [text[i : i + 2] for i in range(0, max(1, len(text)), 2)]
    for token in tokens:
        h = _hash64(token)
        weight = max(1, len(token))
        for bit in range(hash_size):
            if (h >> bit) & 1:
                vector[bit] += weight
            else:
                vector[bit] -= weight
    fingerprint = 0
    for bit in range(hash_size):
        if vector[bit] > 0:
            fingerprint |= 1 << bit
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    """两个 64 位指纹的汉明距离。"""
    return bin(a ^ b).count("1")
