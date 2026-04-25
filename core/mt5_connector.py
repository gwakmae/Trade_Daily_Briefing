# core/mt5_connector.py
# MT5 연결 및 데이터 수집

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from config import BROKERS, SYMBOLS, CANDLE_THRESHOLDS


class MT5Connector:

    def __init__(self, broker_name: str = None):
        from config import DEFAULT_BROKER
        self.broker_name = broker_name or DEFAULT_BROKER
        self.broker_cfg  = BROKERS.get(self.broker_name, {})
        self._connected  = False

    # --------------------------------
    # 연결 / 해제
    # --------------------------------
    def connect(self) -> bool:
        if self.broker_cfg.get("type") != "mt5":
            print(f"[MT5] MT5 브로커가 아님: {self.broker_name}")
            return False

        if not mt5.initialize(path=self.broker_cfg["path"]):
            print(f"[MT5] 초기화 실패: {mt5.last_error()}")
            return False

        if not mt5.login(
            self.broker_cfg["login"],
            self.broker_cfg["password"],
            self.broker_cfg["server"]
        ):
            print(f"[MT5] 로그인 실패: {mt5.last_error()}")
            mt5.shutdown()
            return False

        self._connected = True
        print(f"[MT5] 연결 성공: {self.broker_name}")
        return True

    def disconnect(self):
        mt5.shutdown()
        self._connected = False
        print(f"[MT5] 연결 해제: {self.broker_name}")

    def is_connected(self) -> bool:
        return self._connected

    # --------------------------------
    # 심볼명 조회 (브로커별)
    # --------------------------------
    def get_mt5_symbol(self, display_name: str) -> str:
        for section in SYMBOLS.values():
            if display_name in section:
                return section[display_name].get(self.broker_name, display_name)
        return display_name

    # --------------------------------
    # 일봉 데이터 가져오기
    # --------------------------------
    def get_daily_data(self, display_name: str, count: int = None) -> pd.DataFrame | None:
        if not self._connected:
            print(f"[MT5] 연결되지 않음")
            return None

        count      = count or CANDLE_THRESHOLDS["data_count"]
        mt5_symbol = self.get_mt5_symbol(display_name)

        rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_D1, 0, count)
        if rates is None or len(rates) == 0:
            print(f"[MT5] 데이터 없음: {mt5_symbol} ({mt5.last_error()})")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'time': 'date'})
        df = df[['date', 'open', 'high', 'low', 'close']].copy()
        df = df.reset_index(drop=True)
        return df

    # --------------------------------
    # 전일 인덱스 결정
    # 오늘 캔들이 열렸으면 -2, 아직 없으면 -1
    # --------------------------------
    @staticmethod
    def get_yesterday_idx(df: pd.DataFrame) -> int:
        today            = datetime.today().date()
        last_candle_date = df.iloc[-1]['date'].date()
        return -2 if last_candle_date == today else -1

    # --------------------------------
    # 전체 종목 데이터 일괄 수집
    # --------------------------------
    def fetch_all(self, selected_symbols: list[str]) -> dict:
        results = {}
        for display_name in selected_symbols:
            df = self.get_daily_data(display_name)
            results[display_name] = df
            status = "✓" if df is not None else "✗"
            print(f"  [{self.broker_name}] {display_name} {status}")
        return results
