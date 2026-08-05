"""设计 Token -> QSS 变量映射（单一数据源消费端，禁止手抄颜色）。

从 resources/design-tokens.json 运行时加载，f-string 注入 QSS 模板。
"""

import json
from pathlib import Path

RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
TOKENS_FILE = RESOURCE_DIR / "design-tokens.json"

# 语义化 TOKENS（扁平，供 QSS/代码引用）
TOKENS: dict[str, str] = {}


def load_tokens() -> dict[str, str]:
    """从 design-tokens.json 构建扁平 TOKENS。

    - primitive 为嵌套结构：{category: {key: {value}}}
    - semantic / component 为扁平：{key: {value}}
    """
    with open(TOKENS_FILE, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    flat: dict[str, str] = {}

    def _collect(obj: dict, prefix: str = "") -> None:
        for key, item in obj.items():
            if isinstance(item, dict) and "value" in item:
                flat[f"{prefix}{key}"] = str(item["value"])
            elif isinstance(item, dict):
                _collect(item, f"{prefix}{key}-")

    _collect(raw.get("primitive", {}), "primitive.")
    _collect(raw.get("semantic", {}), "semantic.")
    _collect(raw.get("component", {}), "component.")

    # 快捷语义键（QSS 模板使用）
    for group in ("semantic", "component"):
        for key, item in raw.get(group, {}).items():
            flat[key] = str(item["value"])
    return flat


def _init() -> None:
    global TOKENS
    if not TOKENS:
        TOKENS.update(load_tokens())


_init()

# 高亮色 RGBA（QTextCharFormat 需要整数 RGBA；alpha = 0.xx*255）
HIGHLIGHT_RGBA: dict[str, tuple[int, int, int, int]] = {
    "high": (220, 38, 38, 33),      # rgba(220,38,38,0.13)
    "mid": (234, 88, 12, 31),       # rgba(234,88,12,0.12)
    "cite": (180, 83, 9, 41),       # rgba(180,83,9,0.16)
    "exclude": (107, 114, 128, 26),  # rgba(107,114,128,0.10)
}

FONT_BODY = TOKENS.get("font-body", "sans-serif")
FONT_MONO = TOKENS.get("font-mono", "monospace")

QSS_TEMPLATE = """
/* ===== 全局 ===== */
QWidget {
    background-color: {bg};
    color: {fg};
    font-family: {font_body};
    font-size: 14px;
}

QMainWindow, QDialog { background: {bg}; }

/* ===== 卡片 ===== */
QFrame#Card {
    background: {surface};
    border: 1px solid {border};
    border-radius: {radius_md};
}
QLabel#CardTitle {
    color: {fg}; font-size: 18px; font-weight: 590; padding: 2px 0;
}
QLabel#Muted { color: {muted}; font-size: 13px; }
QLabel#Mono { font-family: {font_mono}; }
QLabel#SectionLabel { color: {fg_2}; font-size: 13px; font-weight: 510; }

/* ===== 按钮 ===== */
QPushButton#Primary {
    background: {accent}; color: {accent_on}; border: none;
    border-radius: {radius_sm}; padding: 8px 16px; min-height: 24px; font-weight: 510;
}
QPushButton#Primary:hover { background: {accent_hover}; }
QPushButton#Primary:pressed { background: {accent_active}; }
QPushButton#Primary:disabled { background: {accent}; color: {accent_on}; }

QPushButton#Secondary {
    background: {surface}; border: 1px solid {border}; border-radius: {radius_sm};
    color: {fg}; padding: 8px 16px; min-height: 24px;
}
QPushButton#Secondary:hover { border-color: {accent}; color: {accent}; }

QPushButton#Ghost {
    background: transparent; border: none; color: {accent};
    padding: 6px 12px; border-radius: {radius_sm};
}
QPushButton#Ghost:hover { background: {accent_soft}; }

QPushButton#DangerGhost {
    background: transparent; border: none; color: {danger};
    padding: 6px 12px; border-radius: {radius_sm};
}
QPushButton#DangerGhost:hover { background: {surface_warm}; }

/* ===== 输入 ===== */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: {surface}; border: 1px solid {border}; border-radius: {radius_sm};
    padding: 6px 10px; min-height: 22px;
    selection-background-color: {accent}; selection-color: {accent_on};
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 2px solid {accent};
}
QLineEdit[error="true"] { border: 1px solid {danger}; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: {surface}; border: 1px solid {border}; selection-background-color: {accent_soft};
    selection-color: {fg};
}

/* ===== Tab ===== */
QTabWidget::pane { border: 1px solid {border}; border-radius: {radius_md}; top: -1px; }
QTabBar::tab {
    background: transparent; color: {muted}; padding: 8px 16px; border-bottom: 2px solid transparent;
}
QTabBar::tab:selected { color: {accent}; border-bottom: 2px solid {accent}; }
QTabBar::tab:hover { color: {accent}; }

/* ===== 表格 ===== */
QTableWidget {
    background: {surface}; border: 1px solid {border}; border-radius: {radius_md};
    gridline-color: {border_soft};
}
QHeaderView::section {
    background: {surface_warm}; color: {fg_2}; border: none;
    border-bottom: 1px solid {border}; padding: 8px; font-weight: 510;
}
QTableWidget::item:selected { background: {accent_soft}; color: {fg}; }

/* ===== 滚动条 ===== */
QScrollBar:vertical { background: {bg}; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: {border}; border-radius: 5px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: {meta}; }
QScrollBar:horizontal { background: {bg}; height: 10px; }
QScrollBar::handle:horizontal { background: {border}; border-radius: 5px; min-width: 32px; }

/* ===== 进度条 ===== */
QProgressBar {
    background: {surface_warm}; border: none; border-radius: 3px;
    text-align: center; color: {fg_2}; height: 6px;
}
QProgressBar::chunk { background: {accent}; border-radius: 3px; }

/* ===== 状态栏 / 徽标 ===== */
QStatusBar { background: {surface}; border-top: 1px solid {border}; color: {muted}; }
QLabel#PrivacyBadge {
    background: {accent_soft}; color: {accent}; border-radius: {radius_pill};
    padding: 4px 12px; font-size: 12px; font-weight: 510;
}
QLabel#Tag {
    background: {surface_warm}; color: {fg_2}; border-radius: {radius_pill};
    padding: 2px 10px; font-size: 12px;
}
QLabel#TagAccent {
    background: {accent_soft}; color: {accent}; border-radius: {radius_pill};
    padding: 2px 10px; font-size: 12px;
}

/* ===== 列表 ===== */
QListWidget, QListWidget#HistoryList {
    background: {surface}; border: 1px solid {border}; border-radius: {radius_md};
}
QListWidget::item { padding: 10px 12px; border-bottom: 1px solid {border_soft}; }
QListWidget::item:hover { background: {surface_warm}; }
QListWidget::item:selected { background: {accent_soft}; color: {fg}; }
"""


def build_qss() -> str:
    """注入 Token 生成最终 QSS。

    用 .replace 而非 str.format（CSS 花括号与 format 冲突）。
    模板占位符同时兼容下划线（font_body）与连字符（font-body）两种写法。
    """
    qss = QSS_TEMPLATE
    for key, value in TOKENS.items():
        qss = qss.replace("{" + key + "}", value)
        qss = qss.replace("{" + key.replace("-", "_") + "}", value)
    return qss


def token(key: str, default: str = "") -> str:
    return TOKENS.get(key, default)


# 语义色速查（UI setStyleSheet 使用，禁止散落硬编码色）
C: dict[str, str] = {
    "bg": token("bg", "#F7F8FA"),
    "surface": token("surface", "#FFFFFF"),
    "surface_warm": token("surface-warm", "#F1F2F4"),
    "fg": token("fg", "#1F2937"),
    "fg_2": token("fg-2", "#4B5563"),
    "muted": token("muted", "#6B7280"),
    "meta": token("meta", "#9CA3AF"),
    "border": token("border", "#E5E7EB"),
    "border_soft": token("border-soft", "#F1F2F4"),
    "accent": token("accent", "#0D9488"),
    "accent_hover": token("accent-hover", "#0F766E"),
    "accent_active": token("accent-active", "#115E59"),
    "accent_on": token("accent-on", "#FFFFFF"),
    "accent_soft": token("accent-soft", "#F0FDFA"),
    "success": token("success", "#16A34A"),
    "warn": token("warn", "#EA580C"),
    "danger": token("danger", "#DC2626"),
    "info": token("info", "#2563EB"),
    "gauge_track": token("gauge-track", "#F1F2F4"),
    "gauge_band": token("gauge-band", "#1FD0C0"),
    "gauge_median": token("gauge-median", "#0D9488"),
    "gauge_threshold": token("gauge-threshold", "#DC2626"),
}


def color(key: str) -> str:
    """取语义色 hex（key 不存在时回退 #000000，避免散落硬编码）。"""
    return C.get(key, "#000000")
