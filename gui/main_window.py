# gui/main_window.py
# 메인 윈도우

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtGui import QFont

from gui.report_tab   import ReportTab
from gui.script_tab   import ScriptTab
from gui.settings_tab import SettingsTab


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TTrades Daily Briefing Tool")
        self.setMinimumSize(900, 700)
        self._init_ui()

    def _init_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10))

        self.report_tab   = ReportTab()
        self.script_tab   = ScriptTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.report_tab,   "📊 리포트")
        self.tabs.addTab(self.script_tab,   "📝 스크립트")
        self.tabs.addTab(self.settings_tab, "⚙ 설정")

        self.setCentralWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

        # 리포트 완료 시 → 스크립트 탭으로 브로커/종목 동기화
        self.report_tab.sync_to_script.connect(self._sync_to_script)

    def _sync_to_script(self, selected: list):
        self.script_tab.sync_from_report(selected)

    def set_status(self, msg: str):
        self.status_bar.showMessage(msg)
