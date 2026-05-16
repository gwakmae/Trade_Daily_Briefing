# gui/report_tab.py
# 리포트 탭
import os
import webbrowser
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar,
    QTextEdit, QSplitter, QCheckBox,
    QDateEdit, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from gui.symbol_selector      import SymbolSelector
from core.report_worker       import ReportWorker
from core.history_manager     import HistoryManager
from config import (
    DEFAULT_BROKER,
    SESSION_CLOSE_HOUR,
    REPORTS_DIR
)

# --------------------------------
# 리포트 탭 UI
# --------------------------------
class ReportTab(QWidget):
    sync_to_script = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.history = HistoryManager()
        self._init_ui()

    def _init_ui(self):
        layout   = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.selector = SymbolSelector(show_broker=True, settings_key="report")
        splitter.addWidget(self.selector)

        right        = QWidget()
        right_layout = QVBoxLayout(right)

        # ── 날짜 선택 그룹 ──
        date_group  = QGroupBox("분석 기준일")
        date_layout = QVBoxLayout(date_group)
        mode_layout = QHBoxLayout()
        self.chk_auto   = QCheckBox("자동")
        self.chk_manual = QCheckBox("수동 지정")
        self.chk_auto.setChecked(True)
        self.chk_auto.toggled.connect(self._on_date_mode_changed)
        self.chk_manual.toggled.connect(self._on_date_mode_changed)
        mode_layout.addWidget(self.chk_auto)
        mode_layout.addWidget(self.chk_manual)
        mode_layout.addStretch()
        date_layout.addLayout(mode_layout)

        cal_layout = QHBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(-1))
        self.date_edit.setEnabled(False)
        self.date_edit.setFixedWidth(130)
        cal_layout.addWidget(QLabel("기준일:"))
        cal_layout.addWidget(self.date_edit)
        cal_layout.addStretch()
        date_layout.addLayout(cal_layout)

        notice = QLabel(
            f"※ 자동: 한국 시간 {SESSION_CLOSE_HOUR:02d}:00 이후 → 전일 마감 봉 기준 / "
            f"{SESSION_CLOSE_HOUR:02d}:00 이전 → 전전일 봉 기준 (전 종목 동일)"
        )
        notice.setStyleSheet("color:#666;font-size:11px;")
        notice.setWordWrap(True)
        date_layout.addWidget(notice)
        right_layout.addWidget(date_group)

        # ── 내보내기 형식 선택 (★ BOTH 옵션 추가) ──
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("📤 내보내기 형식:"))
        self.export_format = QComboBox()
        self.export_format.addItem("HTML (브라우저 열기)", "HTML")
        self.export_format.addItem("PNG (고화질 단일 이미지)", "PNG")
        self.export_format.addItem("HTML + PNG 동시 생성", "BOTH")  # ★ 추가
        self.export_format.setFixedWidth(240)  # ★ 텍스트 길이에 맞게 확장
        fmt_layout.addWidget(self.export_format)
        fmt_layout.addStretch()
        right_layout.addLayout(fmt_layout)

        # ── 실행 버튼 ──
        self.btn_run = QPushButton("📊 리포트 생성")
        self.btn_run.setFixedHeight(44)
        self.btn_run.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_run.setStyleSheet(
            "QPushButton{background:#2563eb;color:white;border-radius:6px}"
            "QPushButton:hover{background:#1d4ed8}"
            "QPushButton:disabled{background:#9ca3af}"
        )
        self.btn_run.clicked.connect(self._run)
        right_layout.addWidget(self.btn_run)

        # ── 폴더 열기 버튼 ──
        self.btn_open_reports = QPushButton("📂 리포트 폴더 열기")
        self.btn_open_reports.setFixedHeight(34)
        self.btn_open_reports.setFont(QFont("Segoe UI", 10))
        self.btn_open_reports.setStyleSheet(
            "QPushButton{background:#4b5563;color:white;border-radius:6px}"
            "QPushButton:hover{background:#374151}"
        )
        self.btn_open_reports.clicked.connect(self._open_reports_folder)
        right_layout.addWidget(self.btn_open_reports)

        # ── 진행 상태 및 로그 ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 9))
        right_layout.addWidget(self.status_label)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        right_layout.addWidget(self.log)

        splitter.addWidget(right)
        splitter.setSizes([350, 550])
        layout.addWidget(splitter)

    def _on_date_mode_changed(self):
        is_manual = self.chk_manual.isChecked()
        self.chk_auto.blockSignals(True)
        self.chk_manual.blockSignals(True)
        self.chk_auto.setChecked(not is_manual)
        self.chk_manual.setChecked(is_manual)
        self.chk_auto.blockSignals(False)
        self.chk_manual.blockSignals(False)
        self.date_edit.setEnabled(is_manual)

    def _get_manual_date(self) -> date | None:
        if self.chk_manual.isChecked():
            qd = self.date_edit.date()
            return date(qd.year(), qd.month(), qd.day())
        return None

    def get_manual_date(self) -> date | None:
        return self._get_manual_date()

    def _open_reports_folder(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        os.startfile(REPORTS_DIR)

    def _run(self):
        selected = self.selector.get_selected()
        if not selected:
            self.status_label.setText("⚠ 종목을 선택하세요.")
            return

        self.btn_run.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log.clear()
        self.status_label.setText("실행 중...")

        manual_date = self._get_manual_date()
        if manual_date:
            self.log.append(f"📅 수동 날짜 지정: {manual_date}")
        else:
            self.log.append(
                f"📅 자동 날짜 판단 "
                f"(한국 시간 {SESSION_CLOSE_HOUR:02d}:00 기준)"
            )

        # 선택된 내보내기 형식 전달
        export_fmt = self.export_format.currentData()  # "HTML", "PNG" 또는 "BOTH"
        self.log.append(f"📤 저장 형식: {export_fmt}")

        self.worker = ReportWorker(selected, manual_date, export_format=export_fmt)
        self.worker.progress.connect(self.log.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, output_path, yesterday_date):
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"✅ 완료: {output_path}")
        self.log.append(f"\n✅ 리포트 저장: {output_path}")
        
        selected = self.selector.get_selected()
        symbols  = [s['display_name'] for s in selected]
        broker   = selected[0]['broker'] if selected else DEFAULT_BROKER
        self.history.add("report", symbols, broker, output_path)
        self.sync_to_script.emit(selected)

        # ★ 내보내기 형식에 따른 열기 방식 분기
        fmt = self.export_format.currentData()
        if fmt == "HTML":
            webbrowser.open(f"file:///{output_path}")      # HTML → 브라우저
        else:  # PNG 또는 BOTH
            os.startfile(REPORTS_DIR)                      # 폴더 열기

    def _on_error(self, msg):
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ 오류 발생")
        self.log.append(f"❌ 오류:\n{msg}")