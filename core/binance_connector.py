# core/binance_connector.py
# Binance API 를 통한 캔들 데이터 수집

import requests
import pandas as pd
from datetime import datetime
from config import BROKERS, SYMBOLS, CANDLE_THRESHOLDS


class BinanceConnector:

    BASE_URL = "https://api.binance.com/api/v3/klines"

    # --------------------------------
    # 심볼명 조회
    # --------------------------------
    def get_binance_symbol(self, display_name: str) -> str | None:
        for section in SYMBOLS.values():
            if display_name in section:
                return section[display_name].get("Binance")
        return None

    # --------------------------------
    # 일봉 데이터 수집
    # --------------------------------
    def get_daily_data(self, display_name: str, count: int = None) -> pd.DataFrame | None:
        count = count or CANDLE_THRESHOLDS["data_count"]
        symbol = self.get_binance_symbol(display_name)
        if not symbol:
            print(f"[Binance] 심볼 없음: {display_name}")
            return None

        try:
            params = {
                "symbol":   symbol,
                "interval": "1d",
                "limit":    count + 1,   # 오늘 미완성 캔들 포함될 수 있어서 +1
            }
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"[Binance] API 오류: {resp.status_code}")
                return None

            raw = resp.json()
            rows = []
            for c in raw:
                rows.append({
                    "date":  pd.to_datetime(c[0], unit="ms"),
                    "open":  float(c[1]),
                    "high":  float(c[2]),
                    "low":   float(c[3]),
                    "close": float(c[4]),
                })

            df = pd.DataFrame(rows)
            df = df.reset_index(drop=True)
            print(f"[Binance] {display_name} ({symbol}) 수집 완료: {len(df)}개")
            return df

        except Exception as e:
            print(f"[Binance] 수집 실패 {display_name}: {e}")
            return None

    # --------------------------------
    # 전일 인덱스 결정 (MT5Connector 와 동일 로직)
    # --------------------------------
    @staticmethod
    def get_yesterday_idx(df: pd.DataFrame) -> int:
        today = datetime.today().date()
        last_candle_date = df.iloc[-1]["date"].date()
        return -2 if last_candle_date == today else -1
