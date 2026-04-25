# gui/history_tab.py
# 기록 탭

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.history_manager import HistoryManager


class HistoryTab(QWidget):

    def __init__(self):
        super().__init__()
        self.history = HistoryManager()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 버튼
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 새로고침")
        self.btn_refresh.clicked.connect(self._load)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["시간", "작업", "종목", "브로커", "출력경로", "메모"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.table)

        self._load()

    def _load(self):
        records = self.history.get_recent(50)
        self.table.setRowCount(len(records))
        for row, rec in enumerate(reversed(records)):
            self.table.setItem(row, 0, QTableWidgetItem(rec.get('timestamp', '')))
            self.table.setItem(row, 1, QTableWidgetItem(rec.get('action', '')))
            self.table.setItem(row, 2, QTableWidgetItem(', '.join(rec.get('symbols', []))))
            self.table.setItem(row, 3, QTableWidgetItem(rec.get('broker', '')))
            self.table.setItem(row, 4, QTableWidgetItem(rec.get('output_path', '')))
            self.table.setItem(row, 5, QTableWidgetItem(rec.get('memo', '')))
