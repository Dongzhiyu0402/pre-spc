"""章节分段：按常见章节标题切分文本。

输出 (section_name, section_text) 列表。不匹配任何标题时整体作为一个 section。
"""

import re

_SECTION_HEADINGS = (
    "摘要",
    "abstract",
    "引言",
    "绪论",
    "introduction",
    "文献综述",
    "相关工作",
    "正文",
    "方法",
    "实验",
    "结果",
    "讨论",
    "结论",
    "conclusion",
    "致谢",
    "acknowledgment",
    "acknowledgements",
)

# 匹配形如 "1 引言" / "一、引言" / "1.1 方法" 的行
_HEADING_LINE = re.compile(r"^\s*(?:\d+(?:\.\d+)*[、.．\s]|[一二三四五六七八九十]+[、.．\s])?(摘要|abstract|引言|绪论|introduction|文献综述|相关工作|正文|方法|实验|结果|讨论|结论|conclusion|致谢|acknowledgment|acknowledgements)\s*[:：]?\s*$", re.IGNORECASE)


def _extract_heading(line: str) -> str | None:
    m = _HEADING_LINE.match(line.strip())
    if not m:
        return None
    return m.group(1).lower()


def split_sections(text: str) -> list[tuple[str, str]]:
    """按章节标题切分。

    返回 [(section_name, section_text), ...]，section_name 为标题原文小写或 "body"。
    """
    return [(name, text[start:end]) for name, start, end in split_sections_with_offsets(text)]


def split_sections_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """按章节标题切分，并返回每个章节在原文中的 [start, end) 字符偏移。

    返回 [(section_name, start, end), ...]。
    """
    if not text.strip():
        return [("全文", 0, len(text))]
    lines = text.split("\n")
    sections: list[tuple[str, int, int]] = []
    current_name = "body"
    current_start = 0
    offset = 0
    for line in lines:
        heading = _extract_heading(line)
        if heading is not None:
            if offset > current_start:
                sections.append((current_name, current_start, offset))
            current_name = heading
            current_start = offset
        offset += len(line) + 1  # +1 换行
    if offset > current_start or not sections:
        sections.append((current_name, current_start, offset))
    return sections
