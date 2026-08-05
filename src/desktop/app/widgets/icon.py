"""Lucide SVG -> QIcon（QSvgRenderer，16/20/24px）。

Lucide 使用 stroke="currentColor"，渲染前替换为目标色（TOKENS 对应值）。
禁 emoji 图标；功能图标全部走此通道。
"""

from functools import lru_cache
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

ICON_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"


@lru_cache(maxsize=None)
def _render_pixmap(name: str, color: str, size: int) -> QPixmap:
    svg_path = ICON_DIR / f"{name}.svg"
    if not svg_path.exists():
        return QPixmap()
    svg_text = svg_path.read_text(encoding="utf-8")
    # 替换 Lucide currentColor 为目标色
    svg_text = svg_text.replace("currentColor", color)

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(svg_text.encode("utf-8"))
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


def icon(name: str, color_name: str = "fg", size: int = 20) -> QIcon:
    """获取着色图标。color_name 为语义色键（如 accent/muted/danger）。"""
    from app.theme import color

    return QIcon(_render_pixmap(name, color(color_name), size))


def icon_button(button, name: str, color: str = "fg", size: int = 20) -> None:
    """给按钮设置图标（setIcon + setIconSize）。"""
    button.setIcon(icon(name, color, size))
    button.setIconSize(QSize(size, size))
