"""桌面端入口：只装配（QApplication + 主题 + 主窗口）。"""

import os
import sys

# 保证 engine/backend 同 src 目录可导入
_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def main() -> int:
    from PyQt6.QtWidgets import QApplication

    from app.store import local_db
    from app.theme import build_qss
    from app.ui.main_window import MainWindow

    local_db.init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("pre-spc")
    app.setStyleSheet(build_qss())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
