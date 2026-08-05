"""桌面端冒烟测试（QT_QPA_PLATFORM=offscreen，无 GUI 环境可跑）。

覆盖：主题构建、主窗口实例化、离线引擎查重、报告渲染、图标渲染。
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PRE_DESKTOP_DATA", str(Path(__file__).resolve().parent / ".test_data"))

_SRC = Path(__file__).resolve().parent.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pytest  # noqa: E402

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from app.theme import build_qss, TOKENS, color  # noqa: E402
from app.store import local_db  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(build_qss())
    return app


def test_theme_tokens_loaded():
    assert TOKENS["accent"] == "#0D9488"
    assert TOKENS["bg"] == "#F7F8FA"
    assert color("danger") == "#DC2626"


def test_qss_builds():
    qss = build_qss()
    assert "QWidget" in qss
    assert "#0D9488" in qss  # accent 注入
    assert "border-radius" in qss


def test_main_window_instantiates(qapp):
    from app.ui.main_window import MainWindow

    win = MainWindow()
    assert win.windowTitle() == "预查重 · 送检前先预估"
    assert win.tabs.count() == 3
    win.close()


def test_local_check_engine(qapp):
    """离线引擎端到端：demo 语料文本 -> 报告结构完整。"""
    from app.services.local_check_service import run_local_check
    from app.services import local_check_service

    # 用 demo 语料写入临时 txt
    demo = Path(__file__).resolve().parent.parent / ".." / "engine" / "data" / "demo_corpus" / "demo_edu_001.txt"
    tmp = Path(__file__).resolve().parent / ".smoke_doc.txt"
    tmp.write_text(demo.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        result = run_local_check(str(tmp), "cnki_sim")
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    assert result["est_low"] <= result["est_median"] <= result["est_high"]
    assert "disclaimer" in result
    assert result["segments"] is not None


def test_report_page_renders(qapp):
    from app.ui.report_page import ReportPage

    page = ReportPage()
    result = {
        "file_name": "demo.txt",
        "plan_code": "cnki_sim",
        "est_median": 18.6,
        "est_low": 14.0,
        "est_high": 24.0,
        "confidence": 82.0,
        "segments": [
            {"start_offset": 0, "end_offset": 10, "highlight_type": "high", "matched_source": "语料库", "similarity": 90.0}
        ],
        "sources": [{"source": "语料库", "count": 1}],
    }
    page.set_report(result)
    assert "18.6%" in page.median_label.text()
    assert "14.0" in page.range_label.text()


def test_icons_render(qapp):
    from app.widgets.icon import icon

    ic = icon("shield-check", "accent", 20)
    assert not ic.isNull()


def test_local_db_roundtrip():
    record_id = local_db.insert_check_record("a.txt", "cnki_sim", {"est_median": 10.0})
    rec = local_db.get_check_record(record_id)
    assert rec is not None
    assert rec["result"]["est_median"] == 10.0
    records = local_db.list_check_records()
    assert any(r["id"] == record_id for r in records)
