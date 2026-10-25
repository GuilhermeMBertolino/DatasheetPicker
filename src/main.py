import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from MainWindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stylesheet_path = Path(__file__).with_name("style.qss")
    check_icon_path = stylesheet_path.with_name("check.svg")
    stylesheet = stylesheet_path.read_text(encoding="utf-8")
    stylesheet = stylesheet.replace(
        "CHECK_ICON_PATH",
        check_icon_path.as_posix(),
    )
    app.setStyleSheet(stylesheet)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())