"""登录 / 注册对话框（居中卡片，错误就近显示，AC-12 注册赠次数）。"""

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.services.api_client import ApiClient, ApiClientError
from app.services import sync_service
from app.theme import color



class LoginDialog(QDialog):
    """登录/注册弹窗。登录成功通过 sync_service 持久化会话。"""

    def __init__(self, api: ApiClient, parent=None) -> None:
        super().__init__(parent)
        self._api = api
        self._mode = "login"
        self._result_data: dict | None = None
        self.setWindowTitle("登录 / 创建账号")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)

        title = QLabel("登录")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        form = QFormLayout()
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("you@example.com")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.nickname_edit = QLineEdit()
        self.nickname_edit.setPlaceholderText("昵称（注册时填写）")
        self.nickname_edit.hide()
        form.addRow("邮箱", self.email_edit)
        form.addRow("密码", self.password_edit)
        form.addRow("昵称", self.nickname_edit)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {color('danger')}; font-size: 13px;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        self.submit_btn = QPushButton("登录")
        self.submit_btn.setObjectName("Primary")
        self.submit_btn.clicked.connect(self._submit)
        layout.addWidget(self.submit_btn)

        self.switch_btn = QPushButton("没有账号？注册")
        self.switch_btn.setObjectName("Ghost")
        self.switch_btn.clicked.connect(self._toggle_mode)
        layout.addWidget(self.switch_btn, alignment=self._center())

        self._apply_mode()

    @staticmethod
    def _center():
        from PyQt6.QtCore import Qt

        return Qt.AlignmentFlag.AlignCenter

    def _apply_mode(self) -> None:
        is_login = self._mode == "login"
        self.nickname_edit.setVisible(not is_login)
        self.submit_btn.setText("登录" if is_login else "注册并领取免费查重次数")
        self.switch_btn.setText("没有账号？注册" if is_login else "已有账号？登录")
        self._title().setText("登录" if is_login else "创建账号")

    def _title(self) -> QLabel:
        return self.findChild(QLabel, "CardTitle")

    def _toggle_mode(self) -> None:
        self._mode = "register" if self._mode == "login" else "login"
        self.error_label.setText("")
        self._apply_mode()

    def _submit(self) -> None:
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        nickname = self.nickname_edit.text().strip() or "user"
        if not email or not password:
            self.error_label.setText("邮箱和密码不能为空")
            return
        try:
            if self._mode == "login":
                data = self._api.login(email, password)
            else:
                if len(password) < 8:
                    self.error_label.setText("密码至少 8 位，建议包含字母和数字")
                    return
                data = self._api.register(email, password, nickname)
        except ApiClientError as exc:
            self.error_label.setText(exc.message)
            return
        sync_service.persist_session(data)
        self._result_data = data
        self.accept()

    def result_data(self) -> dict | None:
        return self._result_data
