# gui/report_tab.py
# 리포트 탭

import webbrowser
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar,
    QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from gui.symbol_selector    import SymbolSelector
from core.mt5_connector     import MT5Connector
from core.binance_connector import BinanceConnector
from core.candle_analyzer   import CandleAnalyzer
from core.report_builder    import ReportBuilder
from core.history_manager   import HistoryManager
from config import DEFAULT_BROKER, BROKERS


# --------------------------------
# 백그라운드 작업 스레드
# --------------------------------
class ReportWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)   # (output_path, yesterday_date)
    error    = pyqtSignal(str)

    def __init__(self, selected: list):
        super().__init__()
        self.selected = selected

    def run(self):
        try:
            today_date     = datetime.today().strftime('%Y-%m-%d')
            yesterday_date = None
            all_data       = {}
            analyzer       = CandleAnalyzer()

            # 브로커별 그룹핑
            broker_groups = {}
            for item in self.selected:
                bn = item['broker']
                if bn not in broker_groups:
                    broker_groups[bn] = []
                broker_groups[bn].append(item['display_name'])

            primary_broker = list(broker_groups.keys())[0]

            for broker_name, symbols in broker_groups.items():
                broker_type = BROKERS.get(broker_name, {}).get("type", "mt5")

                # ---- Binance ----
                if broker_type == "binance":
                    self.progress.emit(f"[Binance] 데이터 수집 중...")
                    conn = BinanceConnector()
                    for display_name in symbols:
                        self.progress.emit(f"  {display_name} 수집 중...")
                        df = conn.get_daily_data(display_name)
                        if df is not None:
                            df = analyzer.analyze(df)
                            all_data[display_name] = df
                            if yesterday_date is None:
                                y_idx          = BinanceConnector.get_yesterday_idx(df)
                                yesterday_date = df.iloc[y_idx]['date'].strftime('%Y-%m-%d')
                            self.progress.emit(f"  {display_name} ✓")
                        else:
                            all_data[display_name] = None
                            self.progress.emit(f"  {display_name} ✗ 데이터 없음")

                # ---- MT5 ----
                else:
                    self.progress.emit(f"[{broker_name}] 연결 중...")
                    conn = MT5Connector(broker_name)
                    if not conn.connect():
                        self.error.emit(f"{broker_name} 연결 실패")
                        return

                    for display_name in symbols:
                        self.progress.emit(f"  {display_name} 수집 중...")
                        df = conn.get_daily_data(display_name)
                        if df is not None:
                            df = analyzer.analyze(df)
                            all_data[display_name] = df
                            if yesterday_date is None:
                                y_idx          = MT5Connector.get_yesterday_idx(df)
                                yesterday_date = df.iloc[y_idx]['date'].strftime('%Y-%m-%d')
                            self.progress.emit(f"  {display_name} ✓")
                        else:
                            all_data[display_name] = None
                            self.progress.emit(f"  {display_name} ✗ 데이터 없음")

                    conn.disconnect()

            if yesterday_date is None:
                yesterday_date = "날짜 확인 불가"

            self.progress.emit("HTML 리포트 생성 중...")
            builder      = ReportBuilder()
            html_content = builder.build(
                all_data, today_date, yesterday_date,
                broker_name=primary_broker
            )
            output_path = builder.save(html_content, today_date)
            self.progress.emit(f"저장 완료: {output_path}")
            self.finished.emit(output_path, yesterday_date)

        except Exception as e:
            import traceback
            self.error.emit(traceback.format_exc())


# --------------------------------
# 리포트 탭 UI
# --------------------------------
class ReportTab(QWidget):

    # 스크립트 탭으로 선택 정보 전달하는 시그널
    sync_to_script = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.history = HistoryManager()
        self._init_ui()

    def _init_ui(self):
        layout   = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 왼쪽: 종목 선택
        self.selector = SymbolSelector(show_broker=True)
        splitter.addWidget(self.selector)

        # 오른쪽: 실행 + 로그
        right        = QWidget()
        right_layout = QVBoxLayout(right)

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

    def _run(self):
        selected = self.selector.get_selected()
        if not selected:
            self.status_label.setText("⚠ 종목을 선택하세요.")
            return

        self.btn_run.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log.clear()
        self.status_label.setText("실행 중...")

        self.worker = ReportWorker(selected)
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

        # 스크립트 탭으로 선택 정보 동기화
        self.sync_to_script.emit(selected)

        webbrowser.open(f"file:///{output_path}")

    def _on_error(self, msg):
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ 오류 발생")
        self.log.append(f"❌ 오류:\n{msg}")
