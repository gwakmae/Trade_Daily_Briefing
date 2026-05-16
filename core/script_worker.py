# core/script_worker.py
# 스크립트 생성 백그라운드 스레드
# gui/script_tab.py 에서 분리

from datetime import date

from PyQt6.QtCore import QThread, pyqtSignal

from config import BROKERS
from core.mt5_connector import MT5Connector
from core.candle_analyzer import CandleAnalyzer
from core.script_builder import ScriptBuilder


class ScriptWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)

    def __init__(self, selected: list, manual_date: date = None):
        super().__init__()
        self.selected    = selected
        self.manual_date = manual_date

    def run(self):
        try:
            analyzer = CandleAnalyzer()
            builder  = ScriptBuilder()
            created  = []

            # 브로커별 그룹핑
            broker_groups = {}
            for item in self.selected:
                broker_name = item["broker"]
                if broker_name not in broker_groups:
                    broker_groups[broker_name] = []
                broker_groups[broker_name].append(item["display_name"])

            for broker_name, symbols in broker_groups.items():
                broker_type = BROKERS.get(broker_name, {}).get("type", "mt5")

                if broker_type == "binance":
                    self.progress.emit("[Binance] MQL5 스크립트 생성 불가 → 건너뜀")
                    continue

                self.progress.emit(f"[{broker_name}] 연결 중...")

                conn = MT5Connector(broker_name)
                if not conn.connect():
                    self.error.emit(f"{broker_name} 연결 실패")
                    return

                for display_name in symbols:
                    self.progress.emit(f"  {display_name} 일봉 데이터 수집 중...")
                    df = conn.get_daily_data(display_name)

                    if df is None:
                        self.progress.emit(f"  {display_name} ✗ 일봉 데이터 없음")
                        continue

                    df = analyzer.analyze(df)
                    self.progress.emit(f"  {display_name} 일봉 데이터 ✓")

                    # 주봉 데이터 수집
                    self.progress.emit(f"  {display_name} 주봉 데이터 수집 중...")
                    wdf = conn.get_weekly_data(display_name)

                    if wdf is not None:
                        weekly_df = analyzer.analyze(wdf)
                        self.progress.emit(f"  {display_name} 주봉 데이터 ✓")
                    else:
                        weekly_df = None
                        self.progress.emit(f"  {display_name} 주봉 데이터 없음 → 일봉 레벨만 생성")

                    # 스크립트 생성
                    filepath = builder.build(
                        display_name=display_name,
                        df=df,
                        broker_name=broker_name,
                        manual_date=self.manual_date,
                        weekly_df=weekly_df,
                    )

                    if filepath:
                        created.append({
                            "path":   filepath,
                            "broker": broker_name,
                            "symbol": display_name,
                        })
                        self.progress.emit(f"  {display_name} 스크립트 생성 ✓ (일봉 + 전주봉 레벨)")
                    else:
                        self.progress.emit(f"  {display_name} 스크립트 생성 실패")

                conn.disconnect()

            self.finished.emit(created)

        except Exception:
            import traceback
            self.error.emit(traceback.format_exc())