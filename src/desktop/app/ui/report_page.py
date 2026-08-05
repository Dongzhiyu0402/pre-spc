"""报告页：预估卡 + 误差带量规 + 章节/片段 + 全文高亮 + 来源 + 导出（AC-05~09）。"""

import html as html_lib
from pathlib import Path

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import load_settings
from app.theme import FONT_MONO, color
from app.widgets.gauge_widget import GaugeWidget
from app.widgets.highlight_text import HighlightTextView
from app.widgets.icon import icon_button

DISCLAIMER = "预估仅供参考，非官方检测报告"


class ReportPage(QWidget):
    """报告页（同构 Web /report/:id）。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._result: dict = {}
        self._full_text: str = ""
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)

        self.title_label = QLabel("查重报告")
        self.title_label.setObjectName("CardTitle")
        outer.addWidget(self.title_label)

        # ---- 预估结果卡 ----
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)

        top = QHBoxLayout()
        left = QVBoxLayout()
        self.median_label = QLabel("--")
        self.median_label.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 48px; color: {color('accent')}; font-weight: 590;")
        left.addWidget(self.median_label)
        self.range_label = QLabel("预估区间 --")
        self.range_label.setObjectName("Muted")
        left.addWidget(self.range_label)
        self.confidence_label = QLabel("")
        self.confidence_label.setObjectName("TagAccent")
        left.addWidget(self.confidence_label)
        top.addLayout(left, 1)

        self.gauge = GaugeWidget()
        top.addWidget(self.gauge, 2)
        card_layout.addLayout(top)

        self.cross_hint = QLabel("")
        self.cross_hint.setStyleSheet(f"background: {color('accent_soft')}; color: {color('accent')}; border-radius: 8px; padding: 10px 12px;")
        self.cross_hint.setWordWrap(True)
        self.cross_hint.hide()
        card_layout.addWidget(self.cross_hint)

        self.wide_hint = QLabel("预估区间较宽，校准样本积累中，结果仅供参考")
        self.wide_hint.setObjectName("Muted")
        self.wide_hint.setWordWrap(True)
        self.wide_hint.hide()
        card_layout.addWidget(self.wide_hint)

        outer.addWidget(card)

        # ---- 导出 + 片段/来源 ----
        tool_row = QHBoxLayout()
        self.export_btn = QPushButton("导出 HTML")
        self.export_btn.setObjectName("Secondary")
        self.export_btn.clicked.connect(self._export_html)
        tool_row.addWidget(self.export_btn)
        tool_row.addStretch(1)
        outer.addLayout(tool_row)

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)

        # 左侧：片段列表 + 全文
        left_panel = QWidget()
        lp = QVBoxLayout(left_panel)
        lp.setContentsMargins(0, 0, 8, 0)
        lp.addWidget(QLabel("相似片段"))
        self.segment_list = QListWidget()
        self.segment_list.currentRowChanged.connect(self._on_segment_selected)
        lp.addWidget(self.segment_list, 1)
        self.text_view = HighlightTextView()
        lp.addWidget(self.text_view, 3)
        splitter.addWidget(left_panel)

        # 右侧：来源
        right_panel = QWidget()
        rp = QVBoxLayout(right_panel)
        rp.setContentsMargins(8, 0, 0, 0)
        rp.addWidget(QLabel("来源提示"))
        self.source_table = QTableWidget(0, 3)
        self.source_table.setHorizontalHeaderLabels(["来源", "命中片段", "相似度"])
        self.source_table.horizontalHeader().setStretchLastSection(True)
        rp.addWidget(self.source_table)
        splitter.addWidget(right_panel)

        splitter.setSizes([720, 320])
        outer.addWidget(splitter, 1)

        disclaimer = QLabel(DISCLAIMER)
        disclaimer.setStyleSheet(f"color: {color('muted')}; font-size: 12px; padding-top: 8px;")
        outer.addWidget(disclaimer)

    def set_report(self, result: dict, full_text: str = "") -> None:
        """载入报告数据（离线 result 或在线 report）。"""
        self._result = result
        self._full_text = full_text
        settings = load_settings()
        threshold = settings.get("threshold", 20)

        median = float(result.get("est_median", 0))
        low = float(result.get("est_low", 0))
        high = float(result.get("est_high", 0))
        confidence = float(result.get("confidence", 0))
        plan_code = result.get("plan_code", "")
        file_name = result.get("file_name", "报告")

        self.title_label.setText(f"查重报告 · {file_name}")
        self.median_label.setText(f"{median:.1f}%")
        self.range_label.setText(f"预估区间 {low:.1f}% – {high:.1f}%")
        self.confidence_label.setText(f"置信度 {confidence:.1f}%")
        self.gauge.set_data(low, median, high, threshold)

        if self.gauge.crosses_threshold():
            self.cross_hint.setText(f"你的预估区间跨过学校阈值 {threshold:.0f}%，建议优先修改高亮片段")
            self.cross_hint.show()
        else:
            self.cross_hint.hide()

        # 宽区间提示（冷启动 / 置信度低）
        if confidence < 60 or result.get("model_status") == "cold_start":
            self.wide_hint.show()
        else:
            self.wide_hint.hide()

        segments = result.get("segments", [])
        self.segment_list.clear()
        type_names = {"high": "高重复", "mid": "中重复", "cite": "引用", "exclude": "已排除"}
        for idx, seg in enumerate(segments):
            htype = type_names.get(seg.get("highlight_type", "mid"), "中重复")
            sim = seg.get("similarity", 0)
            source = seg.get("matched_source", "")
            item = QListWidgetItem(f"[{htype}] {sim:.0f}% · {source}")
            item.setData(256, idx)
            self.segment_list.addItem(item)

        sources = result.get("sources", [])
        self.source_table.setRowCount(0)
        for src in sources:
            row = self.source_table.rowCount()
            self.source_table.insertRow(row)
            self.source_table.setItem(row, 0, QTableWidgetItem(str(src.get("source", ""))))
            self.source_table.setItem(row, 1, QTableWidgetItem(str(src.get("count", 0))))
            self.source_table.setItem(row, 2, QTableWidgetItem("--"))

        if full_text:
            self.text_view.set_content(full_text, segments)
        else:
            # 尝试从本地文件读取原文（原文不出本机，AC-16）
            file_path = result.get("file_path")
            if file_path and Path(file_path).exists():
                try:
                    from engine.cleaning.doc_extractor import extract_text_from_bytes

                    local_text = extract_text_from_bytes(Path(file_path).read_bytes(), Path(file_path).name)
                    self.text_view.set_content(local_text, segments)
                except Exception:  # noqa: BLE001
                    self.text_view.set_content("", [])

    def _on_segment_selected(self, row: int) -> None:
        if row < 0:
            return
        item = self.segment_list.item(row)
        if item is not None:
            self.text_view.locate_segment(row)

    def _export_html(self) -> None:
        """导出 HTML 报告（含免责声明常驻，AC-09）。"""
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(self, "导出报告", "report.html", "HTML (*.html)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._render_html())
        self._show_tip(f"已导出：{path}")

    def _render_html(self) -> str:
        r = self._result
        seg_html = "\n".join(
            f"<li>{html_lib.escape(s.get('matched_source',''))}（{s.get('similarity',0):.1f}%）[{s.get('start_offset',0)}-{s.get('end_offset',0)}] 类型:{s.get('highlight_type','mid')}</li>"
            for s in r.get("segments", [])
        ) or "<li>未发现明显相似片段，继续保持</li>"
        return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>预查重报告</title>
<style>body{{font-family:sans-serif;margin:40px;color:{color('fg')}}} h1{{color:{color('accent')}}} .card{{border:1px solid {color('border')};border-radius:12px;padding:16px;margin:16px 0}} .disc{{background:{color('accent_soft')};padding:12px;border-radius:8px}}</style>
</head><body><h1>预查重报告</h1>
<div class="card"><p><strong>文件:</strong> {html_lib.escape(r.get('file_name',''))}</p>
<p><strong>方案:</strong> {html_lib.escape(r.get('plan_code',''))}</p>
<p><strong>预估中值:</strong> {r.get('est_median',0):.1f}%</p>
<p><strong>预估区间:</strong> {r.get('est_low',0):.1f}% - {r.get('est_high',0):.1f}%</p>
<p><strong>置信度:</strong> {r.get('confidence',0):.1f}%</p></div>
<div class="card"><h2>相似片段</h2><ul>{seg_html}</ul></div>
<div class="disc"><strong>{DISCLAIMER}</strong></div></body></html>"""

    def _show_tip(self, text: str) -> None:
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(self, "提示", text)
