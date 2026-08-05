"""报告指标补算：metrics + chapters（供报告页 UI 扩展字段）。

口径说明（documented，防沉默逻辑错误）：
- exclude_cite_rate：被判定为"引用(cite)"的片段字符数 / 全文总字符数（%）
- exclude_self_rate：去除本人率。MVP 无"本人标记"数据，恒为 None（前端展示"—"）
- max_single_source_rate：单一来源（matched_source 分组）最大命中字符数 / 全文总字符数（%）
- chapters：按章节/段落聚合；无章节结构时给单一 "全文" 条目

确定性：同输入同输出。
"""

from engine.cleaning.section_splitter import split_sections_with_offsets


def _segment_chars(seg: dict, start: int, end: int) -> int:
    """片段与区间 [start,end) 的重叠字符数。"""
    seg_start = max(start, int(seg.get("start_offset", 0)))
    seg_end = min(end, int(seg.get("end_offset", 0)))
    return max(0, seg_end - seg_start)


def compute_metrics(segments: list[dict], doc_length: int) -> dict:
    """按 segments.highlight_type 聚合出三项指标。"""
    doc_length = max(1, doc_length)
    cite_chars = 0
    source_chars: dict[str, int] = {}
    for seg in segments:
        length = _segment_chars(seg, 0, doc_length)
        if seg.get("highlight_type") == "cite":
            cite_chars += length
        source = str(seg.get("matched_source", "未知"))
        source_chars[source] = source_chars.get(source, 0) + length
    max_single = max(source_chars.values(), default=0)
    return {
        "exclude_cite_rate": round(cite_chars / doc_length * 100.0, 2),
        "exclude_self_rate": None,  # 无本人标记数据，口径：MVP 置 null
        "max_single_source_rate": round(max_single / doc_length * 100.0, 2),
    }


def compute_chapters(raw_text: str, segments: list[dict]) -> list[dict]:
    """按章节/段落聚合命中率。

    无章节结构（body 单段）时给单一 "全文" 条目。
    """
    sections = split_sections_with_offsets(raw_text)
    # 无章节结构（单一 body 段）归一为 "全文" 条目
    if len(sections) == 1 and sections[0][0] == "body":
        sections = [("全文", sections[0][1], sections[0][2])]
    chapters: list[dict] = []
    for title, start, end in sections:
        length = max(1, end - start)
        hit_chars = sum(_segment_chars(seg, start, end) for seg in segments)
        rate = min(100.0, round(hit_chars / length * 100.0, 2))
        chapters.append({"title": title, "rate": rate})
    if not chapters:
        chapters = [{"title": "全文", "rate": 0.0}]
    return chapters
