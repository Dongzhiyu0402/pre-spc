"""用量/设置页：账户概览 + 学校阈值 + 校准报告回传（AC-04/07/13/14/15）。"""

import os

from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import load_settings, save_settings
from app.services.api_client import ApiClient, ApiClientError


class UsagePage(QWidget):
    """用量/设置页（同构 Web /usage）。"""

    def __init__(self, nav, parent=None) -> None:
        super().__init__(parent)
        self._nav = nav
        self._report_path: str | None = None
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)

        title = QLabel("用量与设置")
        title.setObjectName("CardTitle")
        outer.addWidget(title)

        # ---- 账户概览 ----
        overview = QFrame()
        overview.setObjectName("Card")
        ov = QVBoxLayout(overview)
        ov.setContentsMargins(20, 16, 20, 16)
        self.mode_label = QLabel("离线模式 · 结果将在联网后同步校准")
        self.mode_label.setObjectName("Muted")
        ov.addWidget(self.mode_label)
        self.session_label = QLabel("未登录（联网后可登录同步）")
        self.session_label.setObjectName("Muted")
        ov.addWidget(self.session_label)
        self.login_btn = QPushButton("登录 / 注册")
        self.login_btn.setObjectName("Secondary")
        self.login_btn.clicked.connect(self._login)
        ov.addWidget(self.login_btn)
        outer.addWidget(overview)

        # ---- 学校阈值 ----
        threshold_card = QFrame()
        threshold_card.setObjectName("Card")
        tc = QVBoxLayout(threshold_card)
        tc.setContentsMargins(20, 16, 20, 16)
        tc.addWidget(QLabel("学校查重率阈值"))
        tc.addWidget(QLabel("报告页的学校阈值线将按此绘制（5-50）"))
        form = QFormLayout()
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(5, 50)
        self.threshold_spin.setValue(20)
        form.addRow("阈值 (%)", self.threshold_spin)
        tc.addLayout(form)
        self.save_threshold_btn = QPushButton("保存阈值")
        self.save_threshold_btn.setObjectName("Primary")
        self.save_threshold_btn.clicked.connect(self._save_threshold)
        tc.addWidget(self.save_threshold_btn)
        outer.addWidget(threshold_card)

        # ---- 校准回传 ----
        cal_card = QFrame()
        cal_card.setObjectName("Card")
        cc = QVBoxLayout(cal_card)
        cc.setContentsMargins(20, 16, 20, 16)
        cc.addWidget(QLabel("回传真实查重报告，让预估更准"))
        cc.addWidget(QLabel("上传你在知网/维普/万方的真实查重报告，我们只提取查重率数字用于校准，回传 1 份送 1 次免费查重"))
        self.cal_file_label = QLabel("未选择报告文件")
        self.cal_file_label.setObjectName("Muted")
        cc.addWidget(self.cal_file_label)
        self.pick_cal_btn = QPushButton("选择报告文件")
        self.pick_cal_btn.setObjectName("Secondary")
        self.pick_cal_btn.clicked.connect(self._pick_cal_file)
        cc.addWidget(self.pick_cal_btn)

        cal_form = QFormLayout()
        self.platform_edit = QLineEdit("cnki")
        self.platform_edit.setPlaceholderText("cnki / vip / wanfang")
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(0, 100)
        cal_form.addRow("平台", self.platform_edit)
        cal_form.addRow("真实查重率 (%)", self.rate_spin)
        cc.addLayout(cal_form)

        self.submit_cal_btn = QPushButton("回传")
        self.submit_cal_btn.setObjectName("Primary")
        self.submit_cal_btn.clicked.connect(self._submit_calibration)
        cc.addWidget(self.submit_cal_btn)

        self.cal_status_label = QLabel("")
        self.cal_status_label.setObjectName("Muted")
        self.cal_status_label.setWordWrap(True)
        cc.addWidget(self.cal_status_label)
        outer.addWidget(cal_card)

        self.tip_label = QLabel("报告文件加密存储，仅用于校准，不会公开")
        self.tip_label.setObjectName("Muted")
        outer.addWidget(self.tip_label)
        outer.addStretch(1)

    def refresh(self) -> None:
        settings = load_settings()
        self.threshold_spin.setValue(int(settings.get("threshold", 20)))
        online = settings.get("online", False)
        user = settings.get("user")
        self.mode_label.setText("在线模式 · 结果以后端为准" if online else "离线模式 · 结果将在联网后同步校准")
        self.session_label.setText(
            f"已登录：{user.get('email', '')}" if online and user else "未登录（联网后可登录同步）"
        )

    def _save_threshold(self) -> None:
        settings = load_settings()
        settings["threshold"] = self.threshold_spin.value()
        save_settings(settings)
        self.cal_status_label.setText("阈值已更新，报告页将按新阈值显示")

    def _login(self) -> None:
        settings = load_settings()
        api = ApiClient(settings["api_base_url"])
        from app.ui.login_page import LoginDialog

        dlg = LoginDialog(api, self)
        if dlg.exec():
            self.refresh()

    def _pick_cal_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择真实查重报告", "", "报告 (*.pdf *.html *.htm *.docx);;所有文件 (*)"
        )
        if path:
            self._report_path = path
            self.cal_file_label.setText(os.path.basename(path))

    def _submit_calibration(self) -> None:
        if not self._report_path:
            self.cal_status_label.setText("请先选择报告文件")
            return
        settings = load_settings()
        if not settings.get("online", False) or not settings.get("access_token"):
            self.cal_status_label.setText("校准回传需要联网并登录，请在设置中先登录")
            return
        platform = self.platform_edit.text().strip()
        if platform not in ("cnki", "vip", "wanfang"):
            self.cal_status_label.setText("平台仅支持 cnki / vip / wanfang")
            return
        api = ApiClient(settings["api_base_url"], settings["access_token"])
        task_id = int(settings.get("last_task_id", 0) or 0)
        if task_id <= 0:
            self.cal_status_label.setText("校准回传需先进行一次在线查重（用于配对预查重结果）")
            return
        try:
            data = api.submit_calibration(self._report_path, platform, float(self.rate_spin.value()), task_id)
            self.cal_status_label.setText("已回传，等待校验。回传 1 份送 1 次免费查重")
        except ApiClientError as exc:
            self.cal_status_label.setText(f"回传失败：{exc.message}")
