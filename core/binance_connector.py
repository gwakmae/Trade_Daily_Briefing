# core/binance_connector.py
# Binance API 를 통한 캔들 데이터 수집

import requests
import pandas as pd
from datetime import datetime, date, timedelta
from config import SYMBOLS, CANDLE_THRESHOLDS, SESSION_CLOSE_HOUR, BINANCE_FUTURES_SYMBOLS


class BinanceConnector:

    # ★ 현물/선물 엔드포인트 분리 (기존 BASE_URL 대체)
    SPOT_BASE_URL    = "https://api.binance.com/api/v3/klines"
    FUTURES_BASE_URL = "https://fapi.binance.com/fapi/v1/klines"

    # --------------------------------
    # 심볼명 조회
    # --------------------------------
    def get_binance_symbol(self, display_name: str) -> str | None:
        for section in SYMBOLS.values():
            if display_name in section:
                return section[display_name].get("Binance")
        return None

    # --------------------------------
    # 공통 데이터 수집 내부 메서드
    # --------------------------------
    def _fetch(self, symbol: str, interval: str,
               limit: int, end_time: int = None) -> pd.DataFrame | None:
        try:
            # ★ 심볼이 선물 목록에 있으면 fapi, 아니면 api(v3) 사용
            base_url = self.FUTURES_BASE_URL if symbol in BINANCE_FUTURES_SYMBOLS else self.SPOT_BASE_URL

            params = {
                "symbol":   symbol,
                "interval": interval,
                "limit":    limit,
            }
            # 이전 1000개를 가져오기 위해 endTime 지정
            if end_time is not None:
                params["endTime"] = end_time

            resp = requests.get(base_url, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"[Binance] API 오류: {resp.status_code}")
                return None

            raw  = resp.json()
            rows = []
            for c in raw:
                rows.append({
                    "date":  pd.to_datetime(c[0], unit="ms", utc=True),
                    "open":  float(c[1]),
                    "high":  float(c[2]),
                    "low":   float(c[3]),
                    "close": float(c[4]),
                })

            df = pd.DataFrame(rows)
            df = df.reset_index(drop=True)
            return df

        except Exception as e:
            print(f"[Binance] 수집 실패 ({symbol}/{interval}): {e}")
            return None

    # --------------------------------
    # 일봉 데이터 수집
    # --------------------------------
    def get_daily_data(self, display_name: str,
                       count: int = None) -> pd.DataFrame | None:
        count  = count or CANDLE_THRESHOLDS["data_count"]
        symbol = self.get_binance_symbol(display_name)
        if not symbol:
            print(f"[Binance] 심볼 없음: {display_name}")
            return None

        df = self._fetch(symbol, "1d", count + 1)
        if df is not None:
            print(f"[Binance] {display_name} ({symbol}) 일봉 수집 완료: {len(df)}개")
        return df

    # --------------------------------
    # 주봉 데이터 수집
    # 전주봉 분석용 — 최근 10주치 수집
    # --------------------------------
    def get_weekly_data(self, display_name: str,
                        count: int = 10) -> pd.DataFrame | None:
        symbol = self.get_binance_symbol(display_name)
        if not symbol:
            print(f"[Binance] 심볼 없음 (주봉): {display_name}")
            return None

        df = self._fetch(symbol, "1w", count + 1)
        if df is not None:
            print(f"[Binance] {display_name} ({symbol}) 주봉 수집 완료: {len(df)}개")
        return df

    # --------------------------------
    # 분봉 데이터 수집 (5분봉 기본)
    # 전일 활발 시간대 분석용
    #
    # Binance kline 의 시간은 UTC 기준 tz-aware
    # → IntradayAnalyzer 에서 source_tz_offset_hours=0 으로 처리
    # --------------------------------
    def get_intraday_data(
        self,
        display_name: str,
        interval: str = "5m",
        count: int = 600,
    ) -> pd.DataFrame | None:
        symbol = self.get_binance_symbol(display_name)
        if not symbol:
            print(f"[Binance] 심볼 없음 (분봉): {display_name}")
            return None

        all_dfs = []
        remaining = count
        end_time = None

        # Binance limit 최대 1000이므로 1000개씩 끊어서 과거로 이동하며 수집
        while remaining > 0:
            limit = min(remaining, 1000)
            df = self._fetch(symbol, interval, limit, end_time)

            if df is None or len(df) == 0:
                break

            all_dfs.append(df)
            remaining -= len(df)

            # 다음 요청을 위해 현재 받은 데이터의 가장 첫 봉(가장 오래된 봉)의 시간에서 1ms 빼기
            first_time_ms = int(df.iloc[0]['date'].timestamp() * 1000)
            end_time = first_time_ms - 1

            # 만약 받은 개수가 요청한 limit보다 적다면 더 이상 과거 데이터가 없는 것
            if len(df) < limit:
                break

        if not all_dfs:
            return None

        # 과거부터 현재 순으로 데이터 병합 후 정렬
        final_df = pd.concat(all_dfs, ignore_index=True)
        final_df = final_df.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)

        print(
            f"[Binance] {display_name} ({symbol}) "
            f"{interval} 수집 완료: {len(final_df)}개"
        )
        return final_df

    # --------------------------------
    # 전일 인덱스 결정
    # 한국 시간 SESSION_CLOSE_HOUR(07:00) 기준
    # --------------------------------
    @staticmethod
    def get_yesterday_idx(df: pd.DataFrame,
                          manual_date: date = None) -> int:
        now = datetime.now()

        if manual_date is not None:
            for i in range(len(df) - 1, -1, -1):
                row_date = df.iloc[i]['date']
                # tz-aware인 경우 KST 날짜로 변환
                if hasattr(row_date, 'tz') and row_date.tz is not None:
                    row_date = row_date.tz_convert('Asia/Seoul').date()
                else:
                    row_date = pd.Timestamp(row_date).date()
                if row_date == manual_date:
                    return i - len(df)
            return -1

        if now.hour >= SESSION_CLOSE_HOUR:
            last_date = df.iloc[-1]['date']
            if hasattr(last_date, 'tz') and last_date.tz is not None:
                last_date = last_date.tz_convert('Asia/Seoul').date()
            else:
                last_date = pd.Timestamp(last_date).date()
            today = now.date()
            return -2 if last_date == today else -1
        else:
            last_date = df.iloc[-1]['date']
            if hasattr(last_date, 'tz') and last_date.tz is not None:
                last_date = last_date.tz_convert('Asia/Seoul').date()
            else:
                last_date = pd.Timestamp(last_date).date()
            today = now.date()
            return -3 if last_date == today else -2

    # --------------------------------
    # 전주 인덱스 결정
    #
    # 바이낸스 주봉 마감 기준:
    #   UTC 일요일 00:00 시작 → 다음 일요일 00:00 마감
    #   KST = UTC + 9h → KST 일요일 09:00 마감
    #   KST 월요일 09:00 이후 직전 주봉이 확정됨
    #
    # ★ 수정:
    #   이전 코드: week_end = week_start + 7일
    #              토/일 보정 후 week_end <= ref 조건
    #              → UTC/KST 경계 미처리로 한 주 밀리는 버그
    #   수정 후:
    #     1) ref = KST 현재 날짜 (reference_date 없을 때)
    #     2) KST 월요일 09:00 이전이면 ref를 일요일로 당김
    #        (아직 직전 주봉 미확정)
    #     3) week_end_kst = week_start_utc (UTC 일요일 = KST 동일 일요일)
    #     4) week_end_kst < ref 조건으로 비교
    # --------------------------------
    @staticmethod
    def get_last_week_idx(df: pd.DataFrame,
                          reference_date: date = None) -> int:
        if df is None or len(df) == 0:
            return -1

        now = datetime.now()

        if reference_date is not None:
            ref = reference_date
            if isinstance(ref, datetime):
                ref = ref.date()
        else:
            ref = now.date()

            # ★ KST 월요일 09:00 이전이면 직전 주봉 미확정
            #   → ref를 일요일(하루 전)로 당겨서 그 이전 주봉을 전주봉으로 사용
            weekday = now.weekday()
            if weekday == 0 and now.hour < 9:   # 월요일 09:00 이전
                ref = ref - timedelta(days=1)   # 일요일로 당김

        for i in range(len(df) - 1, -1, -1):
            raw_date = df.iloc[i]['date']

            # tz-aware이면 UTC 날짜 추출
            if hasattr(raw_date, 'tz') and raw_date.tz is not None:
                week_start_utc = pd.Timestamp(raw_date).tz_convert('UTC').date()
            else:
                week_start_utc = pd.Timestamp(raw_date).date()

            # 바이낸스 주봉: UTC 일요일 00:00 시작
            # KST 마감일 = 동일 날짜의 일요일 09:00 KST
            # → KST 날짜 기준으로 week_end_kst = week_start_utc (동일 일요일)
            week_end_kst = week_start_utc

            # ref가 week_end_kst보다 크면(이후이면) 확정된 전주봉
            if week_end_kst < ref:
                return i - len(df)

        return -1