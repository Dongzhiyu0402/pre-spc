"""全文高亮视图（QTextEdit + QTextCharFormat，对应 --highlight-*）。

- 片段按 highlight_type 映射 RGBA 底色（QColor 支持 alpha）
- 文字保持深色 --fg，保证对比度 4.5:1（desktop-qss §3/§7）
- 提供按原文偏移定位（片段点击联动）
"""

from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QTextEdit

from app.theme import HIGHLIGHT_RGBA, token

from app.theme import color as _theme_color
_FG = QColor(_theme_color("fg"))

# 片段类型 -> 文字标签（WCAG 1.4.1：不只靠颜色传达）
TYPE_LABELS = {
    "high": "高重复",
    "mid": "中重复",
    "cite": "引用",
    "exclude": "已排除",
}


class HighlightTextView(QTextEdit):
    """支持片段高亮与偏移定位的只读全文视图。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptDrops(False)
        self._segments: list[dict] = []
        self._offsets: list[tuple[int, int]] = []  # (doc_position, segment_index)

    def set_content(self, text: str, segments: list[dict]) -> None:
        """渲染全文 + 高亮片段。text 为原始文档文本（片段偏移按原文）。"""
        self._segments = segments
        self._offsets = []
        self.setPlainText("")
        cursor = self.textCursor()

        sorted_segs = sorted(
            [s for s in segments if s.get("end_offset", 0) > s.get("start_offset", 0)],
            key=lambda s: s["start_offset"],
        )
        pos = 0
        for seg in sorted_segs:
            start = max(0, seg["start_offset"])
            end = min(len(text), seg["end_offset"])
            if end <= start:
                continue
            # 片段前普通文本
            cursor.insertText(text[pos:start])
            # 片段高亮 + 前置文字标签
            fmt = self._char_format(seg.get("highlight_type", "mid"))
            cursor.insertText(text[start:end], fmt)
            label = TYPE_LABELS.get(seg.get("highlight_type", "mid"), "")
            if label:
                label_fmt = QTextCharFormat()
                label_fmt.setForeground(_FG)
                label_fmt.setFontPointSize(8)
                cursor.insertText(f" [{label}] ", label_fmt)
            self._offsets.append((start, len(self._offsets)))
            pos = end
        cursor.insertText(text[pos:])
        self.setTextCursor(QTextCursor(cursor))

    def _char_format(self, highlight_type: str) -> QTextCharFormat:
        fmt = QTextCharFormat()
        rgba = HIGHLIGHT_RGBA.get(highlight_type, HIGHLIGHT_RGBA["mid"])
        fmt.setBackground(QColor(*rgba))
        fmt.setForeground(_FG)
        return fmt

    def locate_segment(self, index: int) -> None:
        """滚动定位到第 index 个片段（按起始偏移）。"""
        if not (0 <= index < len(self._offsets)):
            return
        offset, _ = self._offsets[index]
        cur = self.textCursor()
        cur.setPosition(offset)
        self.setTextCursor(cur)
        self.ensureCursorVisible()

    def segment_count(self) -> int:
        return len(self._segments)
