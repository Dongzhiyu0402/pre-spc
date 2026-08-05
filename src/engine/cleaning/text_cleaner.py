"""文本清洗：去页眉页脚/目录/参考文献/非中文字符/空白归一。

规则化清洗，无第三方依赖。
clean_text_with_map 额外返回 清洗文本位置 -> 原文位置 的前向映射，
供引擎把命中片段偏移映射回原文坐标（报告全文高亮 AC-05 需要原文偏移）。
"""

import re

# 常见章节标题（用于截断参考文献等尾部）
_REFERENCE_HEADINGS = (
    "参考文献",
    "reference",
    "references",
    "bibliography",
)

# 页眉页脚常见噪声
_FOOTER_PATTERNS = (
    re.compile(r"第\s*\d+\s*页"),
    re.compile(r"^\s*\d+\s*$"),
    re.compile(r"page\s*\d+", re.IGNORECASE),
)

# 非中文字符、非英文数字、非基本标点 -> 保留中文/英文/数字，其余替换为空格
_NON_CN_ALNUM = re.compile(r"[^\u4e00-\u9fff\u3400-\u4dbfA-Za-z0-9\u3000-\u303f\uff00-\uffef]")

# 空白归一：连续空白 -> 单空格
_WHITESPACE = re.compile(r"\s+")

# 全角转半角映射（常用字符）
_FULLWIDTH_MAP = {0xFF01 + i: 0x21 + i for i in range(94)}


def fullwidth_to_halfwidth(text: str) -> str:
    """全角字符转半角（ASCII 区），提升归一一致性。"""
    return text.translate(_FULLWIDTH_MAP)


def _is_reference_heading(stripped: str) -> bool:
    lowered = stripped.lower()
    return any(lowered == h or lowered.startswith(h + " ") for h in _REFERENCE_HEADINGS)


def _is_footer_or_noise(line: str) -> bool:
    """判断单行是否为页眉页脚/页码噪声。"""
    if not line.strip():
        return False
    for pat in _FOOTER_PATTERNS:
        if pat.search(line.strip()):
            return True
    return False


def _is_toc_marker(line: str) -> bool:
    """目录标记：目录/contents 行、连续点+数字行、纯数字行。"""
    stripped = line.strip()
    if re.match(r"^(目录|contents)\s*$", stripped, re.IGNORECASE):
        return True
    if re.search(r"\.{3,}\s*\d+$", stripped):
        return True
    if re.match(r"^\s*[0-9一二三四五六七八九十]+\s*$", stripped):
        return True
    return False


def _kept_line_spans(text: str, drop_reference: bool) -> list[tuple[int, int]]:
    """计算保留行的原文区间（含行尾换行）。"""
    lines = text.splitlines(keepends=True)
    kept: list[tuple[int, int]] = []
    offset = 0
    in_toc = False
    for line in lines:
        raw_start = offset
        raw_end = offset + len(line)
        offset = raw_end
        stripped = line.strip()
        if _is_footer_or_noise(line):
            continue
        if _is_toc_marker(line):
            # 目录块：目录/contents 行进入 toc 状态，后续 toc 标记行跳过，直到非标记行
            if re.match(r"^(目录|contents)\s*$", stripped, re.IGNORECASE):
                in_toc = True
            continue
        if in_toc:
            # 目录块内：连续 toc 标记行跳过，遇到正文行退出
            if _is_toc_marker(line) or not stripped:
                continue
            in_toc = False
        if drop_reference and _is_reference_heading(stripped):
            break
        kept.append((raw_start, raw_end))
    return kept


def _is_kept_char(ch: str) -> bool:
    """保留中文/英文/数字/常用标点；其余替换为空格。"""
    return not _NON_CN_ALNUM.match(ch)


def clean_text_with_map(text: str, drop_reference: bool = True) -> tuple[str, list[int]]:
    """清洗并返回 (清洗文本, 前向映射)。

    forward_map[i] = 清洗文本第 i 个字符对应的原文下标。
    空白折叠时映射到该空白段的第一个字符下标。
    """
    if not text:
        return "", []
    text = fullwidth_to_halfwidth(text)
    spans = _kept_line_spans(text, drop_reference)
    chars_out: list[tuple[str, int]] = []
    for start, end in spans:
        for idx in range(start, end):
            ch = text[idx]
            if _is_kept_char(ch):
                chars_out.append((ch, idx))
            else:
                chars_out.append((" ", idx))
    cleaned_chars: list[str] = []
    forward_map: list[int] = []
    prev_space = False
    for ch, idx in chars_out:
        is_space = ch == " "
        if is_space:
            if prev_space:
                continue
            prev_space = True
        else:
            prev_space = False
        cleaned_chars.append(ch)
        forward_map.append(idx)
    # 去掉首尾空格（与映射同步裁剪）
    while cleaned_chars and cleaned_chars[0] == " ":
        cleaned_chars.pop(0)
        forward_map.pop(0)
    while cleaned_chars and cleaned_chars[-1] == " ":
        cleaned_chars.pop()
        forward_map.pop()
    return "".join(cleaned_chars), forward_map


def clean_text(text: str, drop_reference: bool = True) -> str:
    """清洗主入口（仅返回清洗文本）。"""
    cleaned, _ = clean_text_with_map(text, drop_reference)
    return cleaned


def map_segments_to_raw(segments: list[dict], forward_map: list[int]) -> list[dict]:
    """把清洗文本坐标的片段映射到原文坐标。

    segments 为 [{start_offset, end_offset, ...}, ...]（清洗文本坐标）。
    返回带原文坐标的新列表，其余字段原样保留。
    """
    mapped: list[dict] = []
    for seg in segments:
        s = seg["start_offset"]
        e = seg["end_offset"]
        if s >= len(forward_map) or e > len(forward_map) or s >= e:
            continue
        raw_start = forward_map[s]
        raw_end = forward_map[e - 1] + 1
        mapped.append({**seg, "start_offset": raw_start, "end_offset": raw_end})
    return mapped
