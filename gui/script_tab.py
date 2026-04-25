# gui/script_tab.py
# 스크립트 탭

import os
import shutil
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit,
    QSplitter, QComboBox, QGroupBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from gui.symbol_selector  import SymbolSelector
from core.mt5_connector   import MT5Connector
from core.candle_analyzer import CandleAnalyzer
from core.script_builder  import ScriptBuilder
from core.history_manager import HistoryManager
from config import DEFAULT_BROKER, BROKERS, SCRIPTS_DIR, load_settings


# --------------------------------
# 백그라운드 스크립트 생성 스레드
# --------------------------------
class ScriptWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)

    def __init__(self, selected: list):
        super().__init__()
        self.selected = selected

    def run(self):
        try:
            analyzer = CandleAnalyzer()
            builder  = ScriptBuilder()
            created  = []

            broker_groups = {}
            for item in self.selected:
                bn = item['broker']
                if bn not in broker_groups:
                    broker_groups[bn] = []
                broker_groups[bn].append(item['display_name'])

            for broker_name, symbols in broker_groups.items():
                broker_type = BROKERS.get(broker_name, {}).get("type", "mt5")

                # Binance 는 스크립트 생성 불가
                if broker_type == "binance":
                    self.progress.emit(f"[Binance] MQL5 스크립트 생성 불가 → 건너뜀")
                    continue

                self.progress.emit(f"[{broker_name}] 연결 중...")
                conn = MT5Connector(broker_name)
                if not conn.connect():
                    self.error.emit(f"{broker_name} 연결 실패")
                    return

                for display_name in symbols:
                    self.progress.emit(f"  {display_name} 데이터 수집 중...")
                    df = conn.get_daily_data(display_name)
                    if df is not None:
                        df       = analyzer.analyze(df)
                        filepath = builder.build(display_name, df, broker_name)
                        if filepath:
                            created.append(filepath)
                            self.progress.emit(f"  {display_name} 스크립트 생성 ✓")
                        else:
                            self.progress.emit(f"  {display_name} 스크립트 생성 실패")
                    else:
                        self.progress.emit(f"  {display_name} ✗ 데이터 없음")

                conn.disconnect()

            self.finished.emit(created)

        except Exception as e:
            import traceback
            self.error.emit(traceback.format_exc())


# --------------------------------
# 스크립트 탭 UI
# --------------------------------
class ScriptTab(QWidget):

    def __init__(self):
        super().__init__()
        self.history        = HistoryManager()
        self._created_files = []
        self._init_ui()

    def _init_ui(self):
        layout   = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽: 종목 선택
        self.selector = SymbolSelector(show_broker=True)
        splitter.addWidget(self.selector)

        # 오른쪽
        right        = QWidget()
        right_layout = QVBoxLayout(right)

        # 스크립트 생성 버튼
        self.btn_run = QPushButton("📝 스크립트 생성")
        self.btn_run.setFixedHeight(44)
        self.btn_run.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_run.setStyleSheet(
            "QPushButton{background:#15803d;color:white;border-radius:6px}"
            "QPushButton:hover{background:#166534}"
            "QPushButton:disabled{background:#9ca3af}"
        )
        self.btn_run.clicked.connect(self._run)
        right_layout.addWidget(self.btn_run)

        # MT5 복사 영역
        copy_group  = QGroupBox("MT5 폴더에 복사")
        copy_layout = QHBoxLayout(copy_group)

        copy_layout.addWidget(QLabel("브로커:"))
        self.copy_broker_combo = QComboBox()
        for name, cfg in BROKERS.items():
            if cfg.get("type") == "mt5":
                self.copy_broker_combo.addItem(name)
        self.copy_broker_combo.setFixedWidth(150)
        copy_layout.addWidget(self.copy_broker_combo)

        self.btn_copy = QPushButton("📁 복사")
        self.btn_copy.setFixedHeight(34)
        self.btn_copy.setFixedWidth(80)
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._copy_to_mt5)
        copy_layout.addWidget(self.btn_copy)

        self.btn_open_output = QPushButton("🗂 output 폴더")
        self.btn_open_output.setFixedHeight(34)
        self.btn_open_output.clicked.connect(lambda: os.startfile(SCRIPTS_DIR))
        copy_layout.addWidget(self.btn_open_output)

        copy_layout.addStretch()
        right_layout.addWidget(copy_group)

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

    # --------------------------------
    # 리포트 탭에서 동기화 수신
    # --------------------------------
    def sync_from_report(self, selected: list):
        # 전체 해제 후 리포트 선택 항목만 체크
        self.selector.deselect_all()

        for item in selected:
            display_name = item['display_name']
            broker       = item['broker']

            # 브로커 콤보 먼저 맞추기 (비활성화 로직 트리거)
            combo = self.selector.broker_combos.get(display_name)
            if combo:
                idx = combo.findText(broker)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

            # 체크박스 체크 (활성화된 경우만)
            cb = self.selector.checkboxes.get(display_name)
            if cb and cb.isEnabled():
                cb.setChecked(True)

        # 복사 브로커 콤보도 첫 번째 MT5 브로커로 맞추기
        if selected:
            for item in selected:
                broker = item['broker']
                if BROKERS.get(broker, {}).get("type") == "mt5":
                    idx = self.copy_broker_combo.findText(broker)
                    if idx >= 0:
                        self.copy_broker_combo.setCurrentIndex(idx)
                    break

        self.log.append("📋 리포트 탭에서 종목/브로커 동기화 완료")

    # --------------------------------
    # 스크립트 생성 실행
    # --------------------------------
    def _run(self):
        selected = self.selector.get_selected()
        if not selected:
            self.status_label.setText("⚠ 종목을 선택하세요.")
            return

        self.btn_run.setEnabled(False)
        self.btn_copy.setEnabled(False)
        self.log.clear()
        self.status_label.setText("실행 중...")

        self.worker = ScriptWorker(selected)
        self.worker.progress.connect(self.log.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, created: list):
        self._created_files = created
        self.btn_run.setEnabled(True)
        self.btn_copy.setEnabled(len(created) > 0)
        self.status_label.setText(f"✅ {len(created)}개 스크립트 생성 완료")
        self.log.append(f"\n✅ 생성된 파일:")
        for path in created:
            self.log.append(f"   {path}")

        selected = self.selector.get_selected()
        symbols  = [s['display_name'] for s in selected]
        broker   = selected[0]['broker'] if selected else DEFAULT_BROKER
        self.history.add("script", symbols, broker, output_path=str(created))

    def _on_error(self, msg):
        self.btn_run.setEnabled(True)
        self.status_label.setText("❌ 오류 발생")
        self.log.append(f"❌ 오류:\n{msg}")

    # --------------------------------
    # MT5 폴더에 복사
    # --------------------------------
    def _copy_to_mt5(self):
        if not self._created_files:
            return

        broker_name = self.copy_broker_combo.currentText()
        settings    = load_settings()
        dest_dir    = settings.get("mt5_scripts_paths", {}).get(broker_name, "")

        if not dest_dir or not os.path.isdir(dest_dir):
            QMessageBox.warning(
                self,
                "경로 미설정",
                f"{broker_name} 의 MT5 Scripts 경로가 설정되지 않았습니다.\n"
                f"설정 탭에서 경로를 지정해주세요."
            )
            return

        copied = 0
        for src in self._created_files:
            try:
                shutil.copy2(src, dest_dir)
                copied += 1
                self.log.append(f"📁 복사됨: {os.path.basename(src)} → {dest_dir}")
            except Exception as e:
                self.log.append(f"❌ 복사 실패: {os.path.basename(src)} ({e})")

        self.status_label.setText(f"✅ {copied}개 파일 복사 완료 → {dest_dir}")
        self.log.append(f"\n✅ 복사 완료: {copied}개 → {dest_dir}")
