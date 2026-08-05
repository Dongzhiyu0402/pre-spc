# 桌面端 QSS 映射要点（PyQt6 消费同一 Token）

> 目的：PyQt6 桌面端用 QSS（Qt Style Sheets）映射 `design-tokens.json`（v1.0.0），与 Web 端视觉零漂移。
> 原则：桌面端是**原生控件观感**（QWidget/QPushButton/QLineEdit/QTabWidget/QTableWidget/QTextEdit），不做网页样式伪装；但配色/间距/圆角/字体严格对齐 Token。
> AntD 不适用于桌面（CSS-in-JS），桌面端只消费 design-tokens.json。

## 1. Token 注入方式（二选一，推荐 A）

- **方式 A（推荐）**：构建时把 design-tokens.json 转成 Python 常量模块 `tokens.py`（脚本生成，禁止手抄），QSS 中用占位符注入：
  ```python
  # tokens.py（由 design-tokens.json 生成，勿手改）
  TOKENS = {
      "accent": "#0D9488", "accent_hover": "#0F766E",
      "bg": "#F7F8FA", "surface": "#FFFFFF", "fg": "#1F2937",
      "fg_2": "#4B5563", "muted": "#6B7280", "meta": "#9CA3AF",
      "border": "#E5E7EB", "border_soft": "#F1F2F4",
      "success": "#16A34A", "warn": "#EA580C", "danger": "#DC2626", "info": "#2563EB",
      "highlight_high": "rgba(220,38,38,0.13)", "highlight_mid": "rgba(234,88,12,0.12)",
      "highlight_cite": "rgba(180,83,9,0.16)", "highlight_exclude": "rgba(107,114,128,0.10)",
      "radius_sm": "8px", "radius_md": "12px", "radius_lg": "16px",
      "font_body": "'Inter','Noto Sans SC','Microsoft YaHei',sans-serif",
      "font_mono": "'JetBrains Mono','Consolas',monospace",
  }
  # QSS 模板：f-string 注入
  qss = QSS_TEMPLATE.format(**TOKENS)
  app.setStyleSheet(qss)
  ```
- 方式 B：运行时常量映射表（同上，仅形式差异）

## 2. QSS 模板骨架（对照 Web Token）

```css
/* ---- 全局 ---- */
QWidget {
    background-color: {bg};            /* ↔ --bg */
    color: {fg};                       /* ↔ --fg */
    font-family: {font_body};          /* ↔ --font-body */
    font-size: 14px;                   /* ↔ --text-sm~md */
}

/* ---- 主窗口/卡片 ---- */
QMainWindow, QDialog { background: {bg}; }
QFrame#Card {
    background: {surface};             /* ↔ --surface */
    border: 1px solid {border};        /* ↔ --border */
    border-radius: {radius_md};        /* ↔ --radius-md 12px */
}

/* ---- 按钮 ---- */
QPushButton#Primary {
    background: {accent};              /* ↔ --accent */
    color: #FFFFFF;                    /* ↔ --accent-on（#fff 例外允许） */
    border: none; border-radius: {radius_sm};  /* ↔ 8px */
    padding: 8px 16px; min-height: 24px;       /* 总高≈40px ↔ --btn-height */
    font-weight: 510;                  /* ↔ --weight-medium */
}
QPushButton#Primary:hover  { background: {accent_hover}; }
QPushButton#Primary:pressed{ background: #115E59; }      /* ↔ --accent-active */
QPushButton#Primary:disabled{ background: #0D9488; opacity: 0.5; }  /* 透明度模拟 */

QPushButton#Secondary {
    background: {surface}; border: 1px solid {border}; border-radius: {radius_sm};
    color: {fg}; padding: 8px 16px; min-height: 24px;
}
QPushButton#Secondary:hover { border-color: {accent}; color: {accent}; }

QPushButton#Ghost {
    background: transparent; border: none; color: {accent};
    padding: 6px 12px; border-radius: {radius_sm};
}
QPushButton#Ghost:hover { background: {accent_soft}; }   /* ↔ --accent-soft */

/* ---- 输入框 ---- */
QLineEdit, QTextEdit {
    background: {surface}; border: 1px solid {border}; border-radius: {radius_sm};
    padding: 8px 12px; min-height: 24px;                 /* 总高≈40px */
    selection-background-color: {accent}; selection-color: #FFFFFF;
}
QLineEdit:focus { border: 2px solid {accent}; }          /* ↔ focus border */
/* 错误态：动态属性 #error { border: 1px solid {danger}; } */
QLineEdit[error="true"] { border: 1px solid {danger}; }

/* ---- Tab ---- */
QTabWidget::pane { border: 1px solid {border}; border-radius: {radius_md}; top: -1px; }
QTabBar::tab {
    background: transparent; color: {muted}; padding: 8px 16px; border-bottom: 2px solid transparent;
}
QTabBar::tab:selected { color: {accent}; border-bottom: 2px solid {accent}; }  /* ↔ 选中态 */

/* ---- 表格（历史/来源列表） ---- */
QTableWidget {
    background: {surface}; border: 1px solid {border}; border-radius: {radius_md};
    gridline-color: {border_soft}; alternate-background-color: {surface};
}
QHeaderView::section {
    background: {surface_warm}; color: {fg_2};           /* ↔ --surface-warm / --fg-2 */
    border: none; border-bottom: 1px solid {border}; padding: 8px; font-weight: 510;
}
QTableWidget::item:selected { background: {accent_soft}; color: {fg}; }

/* ---- 滚动条（可选细化） ---- */
QScrollBar:vertical { background: {bg}; width: 10px; }
QScrollBar::handle:vertical { background: {border}; border-radius: 5px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: {meta}; }

/* ---- 进度条（上传/检测中 ↔ AntD Progress） ---- */
QProgressBar {
    background: {surface_warm}; border: none; border-radius: 3px; text-align: center;
    color: {fg_2}; height: 6px;                            /* ↔ 章节条 6px pill */
}
QProgressBar::chunk { background: {accent}; border-radius: 3px; }
```

## 3. 报告页高亮（QTextEdit + QTextCharFormat，对应 --highlight-*）

```python
from PyQt6.QtGui import QTextCharFormat, QColor
# 映射 design-tokens.json 的 highlight_*（QColor 支持 rgba）
fmt = QTextCharFormat()
fmt.setBackground(QColor(220, 38, 38, 33))   # rgba(220,38,38,0.13) ≈ alpha 33/255 ↔ --highlight-high
# 0.12 → 31；0.16 → 41；0.10 → 26
# 文字保持深色：fmt.setForeground(QColor(31, 41, 55))  # ↔ --fg #1F2937，保证 4.5:1
cursor.mergeCharFormat(fmt)  # 对相似片段 range 应用
# 片段点击定位：QTextEdit 设置 anchor/或保存 offset 映射，点击滚动到对应位置
```

> alpha 换算参考：0.13×255≈33；0.12×255≈31；0.16×255≈41；0.10×255≈26。勿用 CSS 字符串给 QColor，用 RGBA 整数。

## 4. 报告数字对齐（↔ --font-mono + tabular-nums）

- QLabel/QLineEdit 显示查重率/字数/相似比：设 `font-family: {font_mono}`；Qt 无直接 tabular-nums 属性，等宽字体天然对齐（JetBrains Mono 即等宽），满足对齐需求
- 量规：自绘 QWidget（paintEvent 画轨道/色带/中值点/阈值线），颜色取 TOKENS["accent"]/["gauge_*"]；或 QProgressBar 加自定义 paint 叠加区间色带

## 5. 隐私信任（桌面端差异化）

- 顶栏常驻徽标：shield-check 图标（Lucide SVG + QSvgRenderer）+ 文案"本地离线引擎 · 论文不出本机"
- 离线检测时：状态栏显示"离线模式 · 结果将在联网后同步校准"（--muted）

## 6. 图标（Lucide 双端同源）

```python
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QIcon, QPixmap
# 打包 lucide SVG 资源（icons/*.svg），运行时渲染
renderer = QSvgRenderer("icons/shield-check.svg")
pix = QPixmap(24, 24); pix.fill(Qt.GlobalColor.transparent)
painter = QPainter(pix); renderer.render(painter); painter.end()
icon = QIcon(pix)          # 24px 独立图标；按钮内 20px；行内 16px（按需 scale）
# 颜色化：Lucide 用 currentColor/stroke，需替换 stroke 色为 TOKENS 对应值（svg 字符串 replace 后渲染）
```

## 7. QA 检查项（桌面端）

1. QSS 中无硬编码色（唯一例外 #FFFFFF/#000000；TOKENS 注入为准）
2. 无 emoji 图标；图标全部 QSvgRenderer(Lucide)
3. 圆角/间距对齐 Token（8/12/16/pill；4px 网格）
4. 报告高亮仅底色、文字深色、对比度 4.5:1
5. 阈值线/量规/跨线提示与 Web 一致（同一 data + 同一 Token）
6. 隐私徽标常驻

---

*变更记录：v1.0.0 创建（2026-08-05，与 design-tokens.json v1.0.0 配套）*
