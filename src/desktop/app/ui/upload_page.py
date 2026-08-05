"""上传页：拖拽/文件选择 + 方案选择 + 开始检测 + 进度（AC-01/02/03/04/10/11）。"""

import os
import time
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import MAX_UPLOAD_MB, MAX_WORD_COUNT, load_settings, save_settings
from app.services.api_client import ApiClient, ApiClientError
from app.theme import color

from app.services import local_check_service
from app.store import local_db


class CheckWorker(QThread):
    """后台查重线程（离线 engine 或联网 API）。"""

    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, file_path: str, plan_code: str, online: bool, api: ApiClient | None = None) -> None:
        super().__init__()
        self._file_path = file_path
        self._plan_code = plan_code
        self._online = online
        self._api = api

    def run(self) -> None:
        try:
            if self._online and self._api is not None:
                result = self._run_online()
            else:
                result = local_check_service.run_local_check(self._file_path, self._plan_code)
            self.finished_ok.emit(result)
        except local_check_service.CheckError as exc:
            self.failed.emit(str(exc))
        except ApiClientError as exc:
            self.failed.emit(exc.message)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"查重失败: {exc}")

    def _run_online(self) -> dict:
        data = self._api.create_check(self._file_path, self._plan_code)
        task_id = data["task_id"]
        for _ in range(120):  # 最多 120s 轮询
            detail = self._api.get_check(task_id)
            status = detail.get("status")
            if status == "succeeded":
                return self._api.get_report(task_id)
            if status == "failed":
                raise ApiClientError(detail.get("error", "在线查重失败"))
            time.sleep(1)
        raise ApiClientError("在线查重超时")


class UploadPage(QWidget):
    """上传工作台（离线/在线通用）。"""

    def __init__(self, nav, parent=None) -> None:
        super().__init__(parent)
        self._nav = nav
        self._file_path: str | None = None
        self._worker: CheckWorker | None = None
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)

        title = QLabel("上传论文，预估查重率")
        title.setObjectName("CardTitle")
        title.setStyleSheet("font-size: 24px; font-weight: 590;")
        outer.addWidget(title)

        sub = QLabel("送检前先预估，输出预估区间与置信度，省下反复送检的钱")
        sub.setObjectName("Muted")
        outer.addWidget(sub)

        # 方案选择
        plan_row = QHBoxLayout()
        plan_row.addWidget(QLabel("检测方案"))
        self.plan_combo = QListWidget()
        self.plan_combo.setMaximumHeight(96)
        self.plan_combo.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._plans = [
            ("cnki_sim", "知网模拟", "自研模拟"),
            ("vip_sim", "维普模拟", "自研模拟"),
            ("wanfang_sim", "万方模拟", "自研模拟"),
        ]
        for code, name, tag in self._plans:
            self.plan_combo.addItem(f"{name}（{tag}）")
        self.plan_combo.setCurrentRow(0)
        plan_row.addWidget(self.plan_combo, 1)
        outer.addLayout(plan_row)

        # 文件选择行
        file_row = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_label.setObjectName("Muted")
        self.file_label.setWordWrap(True)
        file_row.addWidget(self.file_label, 1)
        self.pick_btn = QPushButton("选择文件")
        self.pick_btn.setObjectName("Secondary")
        self.pick_btn.clicked.connect(self._pick_file)
        file_row.addWidget(self.pick_btn)
        outer.addLayout(file_row)

        hint = QLabel(f"支持 docx / txt / md / pdf · 单文件 ≤{MAX_UPLOAD_MB}MB · ≤{MAX_WORD_COUNT} 字")
        hint.setObjectName("Muted")
        outer.addWidget(hint)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {color('danger')}; font-size: 13px;")
        self.error_label.setWordWrap(True)
        outer.addWidget(self.error_label)

        self.run_btn = QPushButton("开始检测")
        self.run_btn.setObjectName("Primary")
        self.run_btn.setMinimumHeight(44)
        self.run_btn.clicked.connect(self._start)
        outer.addWidget(self.run_btn)

        self.progress = None
        from PyQt6.QtWidgets import QProgressBar

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        outer.addWidget(self.progress)

        privacy = QLabel("文档默认脱敏后入库，可随时删除")
        privacy.setObjectName("Muted")
        outer.addWidget(privacy)
        outer.addStretch(1)

    def _pick_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择论文", "", "论文 (*.docx *.txt *.md *.pdf);;所有文件 (*)"
        )
        if path:
            self._set_file(path)

    def _set_file(self, path: str) -> None:
        self._file_path = path
        self.error_label.setText("")
        self.file_label.setText(f"{Path(path).name}（{os.path.getsize(path) / 1024:.0f} KB）")

    def _start(self) -> None:
        if self._file_path is None:
            self.error_label.setText("请先选择论文文件")
            return
        settings = load_settings()
        online = settings.get("online", False) and bool(settings.get("access_token"))
        plan_code = self._plans[self.plan_combo.currentRow()][0]
        self.run_btn.setEnabled(False)
        self.progress.show()
        self.progress.setValue(20)

        api = None
        if online:
            api = ApiClient(settings["api_base_url"], settings["access_token"])
        self._worker = CheckWorker(self._file_path, plan_code, online, api)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.failed.connect(self._on_error)
        self._worker.start()

    def _on_ok(self, result: dict) -> None:
        self.progress.setValue(100)
        self.run_btn.setEnabled(True)
        # 记录本地文件路径（报告页高亮用；原文不出本机）
        result["file_path"] = self._file_path
        settings = load_settings()
        if settings.get("online", False):
            # 在线任务记录 task_id，供校准回传配对（AC-14）
            if result.get("task_id"):
                settings["last_task_id"] = result["task_id"]
                save_settings(settings)
            record_id = None
        else:
            record_id = local_db.insert_check_record(result.get("file_name", "未命名"), result.get("plan_code", "cnki_sim"), result)
        self._nav.open_report(result, record_id)

    def _on_error(self, message: str) -> None:
        self.progress.hide()
        self.run_btn.setEnabled(True)
        self.error_label.setText(message)
