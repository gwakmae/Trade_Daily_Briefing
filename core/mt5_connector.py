# core/mt5_connector.py
# MT5 연결 및 데이터 수집

import time
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, date, timedelta
from config import BROKERS, SYMBOLS, CANDLE_THRESHOLDS, SESSION_CLOSE_HOUR

# 서머타임 판단 유틸리티 임포트
from core.rth_org_utils import is_us_dst


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
    def get_daily_data(self, display_name: str,
                       count: int = None) -> pd.DataFrame | None:
        if not self._connected:
            print(f"[MT5] 연결되지 않음")
            return None

        count      = count or CANDLE_THRESHOLDS["data_count"]
        mt5_symbol = self.get_mt5_symbol(display_name)

        rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_D1, 0, count)
        if rates is None or len(rates) == 0:
            print(f"[MT5] 일봉 데이터 없음: {mt5_symbol} ({mt5.last_error()})")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'time': 'date'})
        df = df[['date', 'open', 'high', 'low', 'close']].copy()
        df = df.reset_index(drop=True)
        return df

    # --------------------------------
    # 주봉 데이터 가져오기
    # --------------------------------
    def get_weekly_data(self, display_name: str,
                        count: int = 10) -> pd.DataFrame | None:
        if not self._connected:
            print(f"[MT5] 연결되지 않음")
            return None

        mt5_symbol = self.get_mt5_symbol(display_name)

        rates = mt5.copy_rates_from_pos(mt5_symbol, mt5.TIMEFRAME_W1, 0, count)
        if rates is None or len(rates) == 0:
            print(f"[MT5] 주봉 데이터 없음: {mt5_symbol} ({mt5.last_error()})")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'time': 'date'})
        df = df[['date', 'open', 'high', 'low', 'close']].copy()
        df = df.reset_index(drop=True)
        return df

    # --------------------------------
    # 분봉 데이터 가져오기 (5분봉 기본)
    # ★ 수정: UTC tz-aware로 변환하여 intraday_analyzer의
    #         KST 변환이 정확하게 동작하도록 함
    # --------------------------------
    def get_intraday_data(
        self,
        display_name: str,
        timeframe=None,
        count: int = 600,
    ) -> pd.DataFrame | None:
        if not self._connected:
            print(f"[MT5] 연결되지 않음")
            return None

        if timeframe is None:
            timeframe = mt5.TIMEFRAME_M5

        mt5_symbol = self.get_mt5_symbol(display_name)

        rates = mt5.copy_rates_from_pos(mt5_symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            print(f"[MT5] 분봉 데이터 없음: {mt5_symbol} ({mt5.last_error()})")
            return None

        df = pd.DataFrame(rates)

        # ★ 핵심 수정:
        # MT5 copy_rates_from_pos 의 time 컬럼은 UTC 기준 unix timestamp
        # utc=True 로 UTC tz-aware Timestamp Series 로 변환
        # 이후 intraday_analyzer 에서 tz_convert('Asia/Seoul') 로 KST 변환
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'time': 'date'})

        keep_cols = ['date', 'open', 'high', 'low', 'close']
        if 'tick_volume' in df.columns:
            keep_cols.append('tick_volume')

        df = df[keep_cols].copy()
        df = df.reset_index(drop=True)

        # 진단 출력: 첫/마지막 봉 UTC 시각 확인
        print(
            f"[MT5] {display_name} 분봉 수집 완료: {len(df)}개 "
            f"| UTC {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}"
        )
        return df


    # --------------------------------
    # MT5 서버 타임존 오프셋 추정 (단위: 시간)
    # 주말/휴장일에도 서머타임을 고려하여 계산
    # --------------------------------
    def get_server_tz_offset_hours(
        self,
        display_name: str,
        default: float = 2.0,
    ) -> float:
        if not self._connected:
            return default

        # FP / Zero Markets의 미국 서머타임 자동 판단 (기본값 설정)
        is_dst = is_us_dst(datetime.now())
        base_offset = 3.0 if is_dst else 2.0

        candidate_displays = [
            "EURUSD", "USDJPY", "GBPUSD", "BTCUSD", display_name
        ]

        seen = set()
        candidates = []
        for c in candidate_displays:
            if c not in seen:
                seen.add(c)
                candidates.append(c)

        for cand in candidates:
            mt5_symbol = self.get_mt5_symbol(cand)

            try:
                if not mt5.symbol_select(mt5_symbol, True):
                    continue

                rates = mt5.copy_rates_from_pos(
                    mt5_symbol, mt5.TIMEFRAME_M1, 0, 1
                )

                if rates is None or len(rates) == 0:
                    continue

                last_bar_unix = int(rates[0]['time'])
                now_utc_unix  = time.time()

                diff_hours = (last_bar_unix - now_utc_unix) / 3600.0

                if -0.5 <= diff_hours <= 5:
                    offset = float(round(diff_hours))
                    print(
                        f"[MT5] 라이브 타임존 추정 성공: {cand} 마지막봉 기반 "
                        f"GMT+{offset} (raw_diff={diff_hours:.3f}h)"
                    )
                    return offset

            except Exception as e:
                print(f"[MT5] 타임존 추정 시도 실패 ({cand}): {e}")
                continue

        print(
            f"[MT5] 라이브 추정 불가(휴장 등) → US DST 기준 기본값 GMT+{base_offset} 사용"
        )
        return base_offset

    # --------------------------------
    # 전일 인덱스 결정
    # --------------------------------
    @staticmethod
    def get_yesterday_idx(df: pd.DataFrame,
                          manual_date: date = None) -> int:
        now = datetime.now()

        if manual_date is not None:
            for i in range(len(df) - 1, -1, -1):
                if df.iloc[i]['date'].date() == manual_date:
                    return i - len(df)
            return -1

        if now.hour >= SESSION_CLOSE_HOUR:
            last_date = df.iloc[-1]['date'].date()
            today     = now.date()
            return -2 if last_date == today else -1
        else:
            last_date = df.iloc[-1]['date'].date()
            today     = now.date()
            return -3 if last_date == today else -2

    # --------------------------------
    # 전주 인덱스 결정
    #
    # MT5 주봉(TIMEFRAME_W1)의 봉 시작 시각 = 월요일 00:00 서버시간
    # 실제 주봉 마감 = 금요일 종가
    #
    # ★ 수정:
    #   이전 코드: week_end = week_start + 7일 (다음 월요일)
    #              → 경계 조건이 1주 밀려서 5/3 마감 주봉이 전주봉으로 잘못 선택됨
    #   수정 후:   week_friday = week_start + 4일 (금요일 마감일)
    #              week_friday < ref 조건으로 비교
    #              → 금요일 마감이 ref보다 이전이면 그 주가 확정된 전주봉
    # --------------------------------
    @staticmethod
    def get_last_week_idx(df: pd.DataFrame,
                          reference_date: date = None) -> int:
        if df is None or len(df) == 0:
            return -1

        ref = reference_date or datetime.now().date()

        if isinstance(ref, datetime):
            ref = ref.date()

        if hasattr(ref, "date") and not isinstance(ref, date):
            ref = ref.date()

        # 토요일(5)/일요일(6): 이번 주봉을 전주봉으로 간주
        # → ref를 다음 주 월요일로 올려서 이번 주봉의 금요일 마감 이후로 만듦
        weekday = ref.weekday()
        if weekday == 5:        # 토요일 → +2일 (월요일)
            ref = ref + timedelta(days=2)
        elif weekday == 6:      # 일요일 → +1일 (월요일)
            ref = ref + timedelta(days=1)

        for i in range(len(df) - 1, -1, -1):
            week_start  = df.iloc[i]['date'].date()
            # ★ 수정: MT5 주봉 마감은 금요일 (week_start = 월요일 기준)
            week_friday = week_start + timedelta(days=4)

            # 금요일 마감이 ref보다 이전이면 그 주가 확정된 전주봉
            if week_friday < ref:
                return i - len(df)

        return -1
