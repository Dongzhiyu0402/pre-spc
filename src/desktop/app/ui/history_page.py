"""历史页：本地记录列表 + 再次检测（离线为主，联网后以后端为准）。"""

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import PLAN_LABELS
from app.store import local_db


class HistoryPage(QWidget):
    """历史记录页（同构 Web /history）。"""

    def __init__(self, nav, parent=None) -> None:
        super().__init__(parent)
        self._nav = nav
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)

        title = QLabel("历史记录")
        title.setObjectName("CardTitle")
        outer.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("HistoryList")
        self.list_widget.itemDoubleClicked.connect(self._open_selected)
        outer.addWidget(self.list_widget, 1)

        tool_row = QHBoxLayout()
        self.recheck_btn = QPushButton("再次检测")
        self.recheck_btn.setObjectName("Secondary")
        self.recheck_btn.clicked.connect(self._recheck_selected)
        tool_row.addWidget(self.recheck_btn)
        self.delete_btn = QPushButton("删除记录")
        self.delete_btn.setObjectName("DangerGhost")
        self.delete_btn.clicked.connect(self._delete_selected)
        tool_row.addWidget(self.delete_btn)
        tool_row.addStretch(1)
        outer.addLayout(tool_row)

        self.empty_label = QLabel("还没有查重记录，上传第一篇论文试试")
        self.empty_label.setObjectName("Muted")
        self.empty_label.setAlignment(self._center())
        self.empty_label.hide()
        outer.addWidget(self.empty_label)

    @staticmethod
    def _center():
        from PyQt6.QtCore import Qt

        return Qt.AlignmentFlag.AlignCenter

    def refresh(self) -> None:
        records = local_db.list_check_records()
        self.list_widget.clear()
        if not records:
            self.empty_label.show()
            return
        self.empty_label.hide()
        for rec in records:
            result = rec.get("result", {})
            median = result.get("est_median", 0)
            plan = PLAN_LABELS.get(rec.get("plan_code", ""), rec.get("plan_code", ""))
            text = f"{rec['file_name']}  ·  {plan}  ·  预估 {median:.1f}%  ·  {rec['created_at']}"
            item = QListWidgetItem(text)
            item.setData(256, rec["id"])
            self.list_widget.addItem(item)

    def _open_selected(self, item: QListWidgetItem) -> None:
        record_id = item.data(256)
        rec = local_db.get_check_record(record_id)
        if rec:
            self._nav.open_report(rec.get("result", {}), rec["id"])

    def _selected_record_id(self) -> int | None:
        item = self.list_widget.currentItem()
        return item.data(256) if item else None

    def _recheck_selected(self) -> None:
        record_id = self._selected_record_id()
        if record_id:
            self._recheck(record_id)

    def _delete_selected(self) -> None:
        record_id = self._selected_record_id()
        if record_id:
            local_db.delete_record(record_id)
            self.refresh()

    def _recheck(self, record_id: int) -> None:
        rec = local_db.get_check_record(record_id)
        if not rec:
            return
        result = rec.get("result", {})
        file_path = result.get("file_path")
        plan_code = rec.get("plan_code", "cnki_sim")
        if not file_path:
            return
        from app.services import local_check_service

        try:
            new_result = local_check_service.run_local_check(file_path, plan_code)
            new_result["file_path"] = file_path
            new_id = local_db.insert_check_record(rec["file_name"], plan_code, new_result)
            self._nav.open_report(new_result, new_id)
        except local_check_service.CheckError as exc:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "再次检测失败", str(exc))
