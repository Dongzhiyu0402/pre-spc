"""误差带量规（AC-06/07）：QPainter 自绘。

元素：轨道 / 区间色带 [est_low, est_high] / 中值点 / 阈值线 / 端点文字 / 标尺。
颜色全部来自 design-tokens（禁硬编码色）。
"""

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from app.theme import color, FONT_MONO


def _color(key: str) -> QColor:
    return QColor(color(key))


class GaugeWidget(QWidget):
    """横向误差带量规。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._est_low = 0.0
        self._est_median = 0.0
        self._est_high = 0.0
        self._threshold: float | None = None
        self.setMinimumHeight(96)

    def set_data(self, est_low: float, est_median: float, est_high: float, threshold: float | None = None) -> None:
        self._est_low = max(0.0, min(100.0, est_low))
        self._est_median = max(0.0, min(100.0, est_median))
        self._est_high = max(0.0, min(100.0, est_high))
        if self._est_low > self._est_high:
            self._est_low, self._est_high = self._est_high, self._est_low
        self._threshold = threshold
        self.update()

    def crosses_threshold(self) -> bool:
        return self._threshold is not None and self._est_high > self._threshold

    # ---- 坐标换算 ----
    def _x(self, value: float) -> float:
        w = self.width() - 40.0
        return 20.0 + value / 100.0 * w

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        track_color = _color("gauge_track")
        band_color = _color("gauge_band")
        median_color = _color("gauge_median")
        threshold_color = _color("gauge_threshold")
        muted = _color("muted")
        meta = _color("meta")

        # 标尺刻度
        painter.setPen(QPen(meta, 1))
        font_small = QFont(FONT_MONO, 8)
        painter.setFont(font_small)
        for tick in (0, 25, 50, 75, 100):
            tx = self._x(tick)
            painter.drawLine(int(tx), 28, int(tx), 34)
            painter.drawText(QRectF(int(tx) - 25, 36, 50, 16), Qt.AlignmentFlag.AlignCenter, f"{tick}%")

        # 轨道（粗 pill）
        track_rect = QRectF(20, 44, w - 40, 10)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, 5, 5)

        # 区间色带（覆盖 [low, high]，较轨道高）
        if self._est_high > self._est_low:
            band_rect = QRectF(self._x(self._est_low), 40, self._x(self._est_high) - self._x(self._est_low), 18)
            painter.setBrush(band_color)
            painter.drawRoundedRect(band_rect, 5, 5)

        # 中值点 + 引导线
        mx = self._x(self._est_median)
        painter.setPen(QPen(median_color, 2))
        painter.drawLine(int(mx), 24, int(mx), 62)
        painter.setBrush(median_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(mx) - 7, 36, 14, 14)

        # 端点文字（mono）
        painter.setPen(QPen(muted, 1))
        low_text = f"{self._est_low:.1f}%"
        high_text = f"{self._est_high:.1f}%"
        painter.drawText(QRectF(0, 66, 90, 20), Qt.AlignmentFlag.AlignLeft, low_text)
        painter.drawText(QRectF(w - 90, 66, 90, 20), Qt.AlignmentFlag.AlignRight, high_text)

        # 阈值线（红虚线 + 标签）
        if self._threshold is not None and 0 < self._threshold < 100:
            tx = self._x(self._threshold)
            pen = QPen(threshold_color, 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(int(tx), 22, int(tx), 60)
            painter.setPen(QPen(threshold_color, 1))
            painter.drawText(QRectF(int(tx) - 70, 2, 140, 18), Qt.AlignmentFlag.AlignCenter, f"学校阈值 {self._threshold:.0f}%")

        painter.end()
