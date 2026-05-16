# gui/script_tab.py
# 스크립트 탭
# 일봉 + 주봉 데이터 기반 MQL5 스크립트 생성

import os
import shutil
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit,
    QSplitter, QGroupBox,
    QCheckBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from gui.symbol_selector  import SymbolSelector
from core.script_worker   import ScriptWorker           # ← 변경
from core.history_manager import HistoryManager
from config import (
    DEFAULT_BROKER, BROKERS, SCRIPTS_DIR,
    SESSION_CLOSE_HOUR, load_settings
)


# --------------------------------
# 스크립트 탭 UI
# --------------------------------
class ScriptTab(QWidget):

    def __init__(self):
        super().__init__()

        self.history        = HistoryManager()
        self._created_files = []

        # 브로커별 복사 버튼 / 카운트 라벨
        self.copy_buttons        = {}
        self.open_dest_buttons   = {}
        self.broker_count_labels = {}

        self._init_ui()

    def _init_ui(self):
        layout   = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽: 종목 선택
        self.selector = SymbolSelector(show_broker=True, settings_key="script")
        splitter.addWidget(self.selector)

        # 오른쪽
        right        = QWidget()
        right_layout = QVBoxLayout(right)

        # ── 날짜 선택 영역 ──
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

        # ── 스크립트 생성 버튼 ──
        self.btn_run = QPushButton("📜 스크립트 생성")
        self.btn_run.setFixedHeight(44)
        self.btn_run.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_run.setStyleSheet(
            "QPushButton{background:#15803d;color:white;border-radius:6px}"
            "QPushButton:hover{background:#166534}"
            "QPushButton:disabled{background:#9ca3af}"
        )
        self.btn_run.clicked.connect(self._run)
        right_layout.addWidget(self.btn_run)

        # ── MT5 복사 영역 ──
        copy_group  = QGroupBox("MT5 폴더에 복사")
        copy_layout = QVBoxLayout(copy_group)

        info = QLabel(
            "각 버튼은 해당 브로커로 생성된 스크립트만 그 브로커의 MT5 Scripts 폴더로 복사합니다."
        )
        info.setStyleSheet("color:#666;font-size:11px;")
        info.setWordWrap(True)
        copy_layout.addWidget(info)

        for broker_name, cfg in BROKERS.items():
            if cfg.get("type") != "mt5":
                continue

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)

            lbl = QLabel(broker_name)
            lbl.setFixedWidth(110)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            row_layout.addWidget(lbl)

            count_label = QLabel("생성 0개")
            count_label.setFixedWidth(70)
            count_label.setStyleSheet("color:#666;font-size:11px;")
            self.broker_count_labels[broker_name] = count_label
            row_layout.addWidget(count_label)

            btn_copy = QPushButton("📋 복사")
            btn_copy.setFixedWidth(80)
            btn_copy.setFixedHeight(30)
            btn_copy.setEnabled(False)
            btn_copy.clicked.connect(
                lambda checked, bn=broker_name: self._copy_to_broker(bn)
            )
            self.copy_buttons[broker_name] = btn_copy
            row_layout.addWidget(btn_copy)

            btn_open_dest = QPushButton("📂 Scripts 폴더 열기")
            btn_open_dest.setFixedWidth(140)
            btn_open_dest.setFixedHeight(30)
            btn_open_dest.clicked.connect(
                lambda checked, bn=broker_name: self._open_broker_scripts_folder(bn)
            )
            self.open_dest_buttons[broker_name] = btn_open_dest
            row_layout.addWidget(btn_open_dest)

            row_layout.addStretch()
            copy_layout.addWidget(row)

        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 6, 0, 0)

        self.btn_open_output = QPushButton("🗂 생성 output 폴더 열기")
        self.btn_open_output.setFixedHeight(32)
        self.btn_open_output.clicked.connect(lambda: os.startfile(SCRIPTS_DIR))
        bottom_layout.addWidget(self.btn_open_output)

        bottom_layout.addStretch()
        copy_layout.addWidget(bottom_row)

        right_layout.addWidget(copy_group)

        # ── 상태 / 로그 ──
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

        self._update_copy_buttons()

    # ── 날짜 모드 변경 ──
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

    # ── 리포트 탭에서 동기화 수신 ──
    def sync_from_report(self, selected: list, manual_date: date = None):
        self.selector.deselect_all()

        for item in selected:
            display_name = item["display_name"]
            broker       = item["broker"]

            combo = self.selector.broker_combos.get(display_name)
            if combo:
                idx = combo.findText(broker)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

            cb = self.selector.checkboxes.get(display_name)
            if cb and cb.isEnabled():
                cb.setChecked(True)

        if manual_date is not None:
            self.chk_manual.setChecked(True)
            self.date_edit.setDate(
                QDate(manual_date.year, manual_date.month, manual_date.day)
            )
        else:
            self.chk_auto.setChecked(True)

        self.selector._save_selection()
        self.log.append("📋 리포트 탭에서 종목/브로커/날짜 동기화 완료")

    # ── 스크립트 생성 실행 ──
    def _run(self):
        selected = self.selector.get_selected()

        if not selected:
            self.status_label.setText("⚠ 종목을 선택하세요.")
            return

        self.btn_run.setEnabled(False)
        self._created_files = []
        self._update_copy_buttons()

        self.log.clear()
        self.status_label.setText("실행 중...")

        manual_date = self._get_manual_date()

        if manual_date:
            self.log.append(f"📅 수동 날짜 지정: {manual_date}")
        else:
            self.log.append(
                f"📅 자동 날짜 판단 (한국 시간 {SESSION_CLOSE_HOUR:02d}:00 기준)"
            )

        self.worker = ScriptWorker(selected, manual_date)
        self.worker.progress.connect(self.log.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    # ── 생성 완료 ──
    def _on_finished(self, created: list):
        self._created_files = created

        self.btn_run.setEnabled(True)
        self._update_copy_buttons()

        self.status_label.setText(f"✅ {len(created)}개 스크립트 생성 완료")
        self.log.append("\n✅ 생성된 파일:")

        output_paths = []

        for item in created:
            path   = item.get("path", "")
            broker = item.get("broker", "")
            symbol = item.get("symbol", "")

            output_paths.append(path)
            self.log.append(f"   [{broker} / {symbol}] {path}")

        selected = self.selector.get_selected()
        symbols  = [s["display_name"] for s in selected]
        broker   = selected[0]["broker"] if selected else DEFAULT_BROKER

        self.history.add("script", symbols, broker, output_path=str(output_paths))

    # ── 오류 ──
    def _on_error(self, msg):
        self.btn_run.setEnabled(True)
        self.status_label.setText("❌ 오류 발생")
        self.log.append(f"❌ 오류:\n{msg}")
        self._update_copy_buttons()

    # ── 브로커별 생성 파일 개수 ──
    def _count_created_by_broker(self, broker_name: str) -> int:
        return sum(
            1 for item in self._created_files
            if item.get("broker") == broker_name
        )

    # ── 복사 버튼 상태 갱신 ──
    def _update_copy_buttons(self):
        for broker_name, btn in self.copy_buttons.items():
            count = self._count_created_by_broker(broker_name)
            btn.setEnabled(count > 0)

            label = self.broker_count_labels.get(broker_name)
            if label:
                label.setText(f"생성 {count}개")

    # ── 특정 브로커로 생성된 파일만 복사 ──
    def _copy_to_broker(self, broker_name: str):
        if not self._created_files:
            self.status_label.setText("⚠ 복사할 스크립트가 없습니다.")
            return

        settings = load_settings()
        paths    = settings.get("mt5_scripts_paths", {})

        dest_dir = paths.get(broker_name, "").strip()

        if not dest_dir or not os.path.isdir(dest_dir):
            self.status_label.setText(f"⚠ {broker_name} Scripts 경로 미설정")
            self.log.append(
                f"⚠ {broker_name} 의 MT5 Scripts 경로가 설정되지 않았습니다.\n"
                f"   설정 탭에서 {broker_name} 경로를 지정하세요."
            )
            return

        targets = [
            item for item in self._created_files
            if item.get("broker") == broker_name
        ]

        if not targets:
            self.status_label.setText(f"⚠ {broker_name} 로 생성된 스크립트가 없습니다.")
            self.log.append(f"⚠ {broker_name} 로 생성된 스크립트가 없습니다.")
            return

        copied  = 0
        skipped = 0

        self.log.append(f"\n📋 [{broker_name}] 복사 시작 → {dest_dir}")

        for item in targets:
            src    = item.get("path", "")
            symbol = item.get("symbol", "")

            if not src or not os.path.isfile(src):
                skipped += 1
                self.log.append(f"❌ 원본 파일 없음: [{symbol}] {src}")
                continue

            try:
                shutil.copy2(src, dest_dir)
                copied += 1
                self.log.append(f"   ✓ [{symbol}] {os.path.basename(src)} → {dest_dir}")
            except Exception as e:
                skipped += 1
                self.log.append(f"   ❌ [{symbol}] 복사 실패: {os.path.basename(src)} ({e})")

        self.status_label.setText(
            f"✅ {broker_name}: {copied}개 복사 완료 / {skipped}개 건너뜀"
        )
        self.log.append(f"✅ [{broker_name}] 복사 완료: {copied}개 / 건너뜀: {skipped}개")

    # ── 브로커 MT5 Scripts 폴더 열기 ──
    def _open_broker_scripts_folder(self, broker_name: str):
        settings = load_settings()
        paths    = settings.get("mt5_scripts_paths", {})

        dest_dir = paths.get(broker_name, "").strip()

        if not dest_dir or not os.path.isdir(dest_dir):
            self.status_label.setText(f"⚠ {broker_name} Scripts 경로 미설정")
            self.log.append(
                f"⚠ {broker_name} 의 MT5 Scripts 경로가 설정되지 않았습니다.\n"
                f"   설정 탭에서 {broker_name} 경로를 지정하세요."
            )
            return

        os.startfile(dest_dir)