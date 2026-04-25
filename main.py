# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Malgun Gothic", 10))
    app.setStyle("Fusion")

    # 아이콘 설정
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
