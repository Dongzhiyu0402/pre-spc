"""主窗口：导航（TabWidget）+ 顶栏隐私徽标 + 联网/离线切换。"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import load_settings, save_settings
from app.services import sync_service
from app.store import local_db
from app.theme import color
from app.ui.history_page import HistoryPage
from app.ui.report_page import ReportPage
from app.ui.upload_page import UploadPage
from app.ui.usage_page import UsagePage

PRIVACY_TEXT = "本地离线引擎 · 论文不出本机"


class MainWindow(QMainWindow):
    """桌面端主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("预查重 · 送检前先预估")
        self.resize(1080, 760)
        self._build()
        local_db.init_db()
        self.usage_page.refresh()
        self.history_page.refresh()

    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶栏：品牌 + 隐私徽标 + 模式切换
        header = QWidget()
        header.setStyleSheet(f"background: {color('surface')}; border-bottom: 1px solid {color('border')};")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(20, 10, 20, 10)

        brand = QLabel("预查重")
        brand.setStyleSheet(f"font-size: 18px; font-weight: 590; color: {color('accent')};")
        hh.addWidget(brand)

        privacy = QLabel(PRIVACY_TEXT)
        privacy.setObjectName("PrivacyBadge")
        hh.addWidget(privacy)

        hh.addStretch(1)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["离线模式", "在线模式"])
        settings = load_settings()
        self.mode_combo.setCurrentIndex(1 if settings.get("online", False) else 0)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        hh.addWidget(self.mode_combo)

        root.addWidget(header)

        # Tab 导航
        self.tabs = QTabWidget()
        self.upload_page = UploadPage(self)
        self.report_page = ReportPage()
        self.history_page = HistoryPage(self)
        self.usage_page = UsagePage(self)
        self.tabs.addTab(self.upload_page, "上传检测")
        self.tabs.addTab(self.history_page, "历史记录")
        self.tabs.addTab(self.usage_page, "用量与设置")
        root.addWidget(self.tabs, 1)

        # 状态栏
        self.statusBar().showMessage("离线模式 · 结果将在联网后同步校准")

    def _on_mode_changed(self, index: int) -> None:
        settings = load_settings()
        settings["online"] = index == 1
        save_settings(settings)
        self.statusBar().showMessage("在线模式 · 结果以后端为准" if index == 1 else "离线模式 · 结果将在联网后同步校准")
        self.usage_page.refresh()

    # ---- 导航回调 ----
    def open_report(self, result: dict, record_id: int | None = None) -> None:
        self.report_page.set_report(result)
        self.tabs.setCurrentWidget(self.report_page)

    def open_history(self) -> None:
        self.history_page.refresh()
        self.tabs.setCurrentWidget(self.history_page)
