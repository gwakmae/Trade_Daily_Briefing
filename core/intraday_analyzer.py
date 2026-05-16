# core/intraday_analyzer.py
# 분봉 데이터를 시간대(KST) 단위로 집계하여
# 가격 변동이 활발한 시간대를 산출

import pandas as pd
from datetime import date


class IntradayAnalyzer:
    """
    전일 5분봉을 받아서:
      1) 소스 시간 → KST 변환
      2) 시간(0~23) 단위로 평균 변동폭(high-low) 계산
      3) TOP 3 시간대 + 24시간 분포 반환

    ★ 수정:
      MT5/Binance 모두 UTC tz-aware datetime('date' 컬럼)으로 통일
      tz-aware 여부를 안전하게 확인 후 KST 변환
    """

    # --------------------------------
    # 메인: 전일 분봉 → 시간대별 활성도
    # --------------------------------
    def analyze(
        self,
        df: pd.DataFrame,
        target_date: date,
        source_tz_offset_hours: float = 0.0,
        top_n: int = 3,
    ) -> dict | None:
        """
        전일 5분봉 → 시간대별 활성도 분석

        거래일 정의 (★ 변경):
        KST 07:00 (아시아 세션 시작) ~ 익일 KST 06:59 (뉴욕 세션 종료)
        distribution 순서도 07, 08, ..., 23, 00, ..., 06 으로 정렬되어
        아시아→유럽→뉴욕 시간 흐름으로 막대그래프 표시됨
        """
        if df is None or len(df) == 0:
            return None

        df = df.copy()

        # ─────────────────────────────────────────
        # KST 변환
        # ─────────────────────────────────────────
        raw = df['date']

        try:
            is_tz_aware = (
                hasattr(raw.dtype, 'tz') and raw.dtype.tz is not None
            )
        except Exception:
            is_tz_aware = False

        if is_tz_aware:
            # UTC tz-aware → KST 직접 변환 후 tz 제거
            df['kst'] = raw.dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
        else:
            # tz-naive → offset 보정해서 KST로
            kst_shift = 9.0 - source_tz_offset_hours
            df['kst'] = pd.to_datetime(raw) + pd.Timedelta(hours=kst_shift)

        # 진단용
        kst_first = df['kst'].iloc[0]
        kst_last  = df['kst'].iloc[-1]

        # ─────────────────────────────────────────
        # 거래일 필터: KST 07:00 ~ 익일 06:59
        # ─────────────────────────────────────────
        day_start = pd.Timestamp(target_date) + pd.Timedelta(hours=7)
        day_end   = day_start + pd.Timedelta(days=1)

        day_df = df[(df['kst'] >= day_start) & (df['kst'] < day_end)].copy()

        if len(day_df) == 0:
            return {
                '_diag': {
                    'kst_first':       str(kst_first),
                    'kst_last':        str(kst_last),
                    'target_date':     str(target_date),
                    'day_start':       str(day_start),
                    'day_end':         str(day_end),
                    'matched_candles': 0,
                    'tz_offset_used':  source_tz_offset_hours,
                    'tz_aware':        is_tz_aware,
                },
                'target_date':   target_date.strftime('%Y-%m-%d'),
                'total_candles': 0,
                'top':           [],
                'distribution':  [],
            }

        # 변동폭 계산
        day_df['range'] = day_df['high'] - day_df['low']
        day_df['hour']  = day_df['kst'].dt.hour

        # 시간대별 평균 변동폭
        hourly = (
            day_df.groupby('hour')['range']
            .agg(['mean', 'max', 'count'])
            .reset_index()
        )
        hourly.columns = ['hour', 'avg_range', 'max_range', 'count']

        # ★ 변경: 07~06 순서로 정렬
        # 07, 08, ..., 23, 00, 01, ..., 06
        trading_hours = list(range(7, 24)) + list(range(0, 7))
        full = pd.DataFrame({'hour': trading_hours})
        hourly = full.merge(hourly, on='hour', how='left', sort=False).fillna(0)

        # TOP N
        top_df = (
            hourly[hourly['avg_range'] > 0]
            .sort_values('avg_range', ascending=False)
            .head(top_n)
        )
        top = []
        for _, row in top_df.iterrows():
            top.append({
                'hour':      int(row['hour']),
                'avg_range': float(row['avg_range']),
                'max_range': float(row['max_range']),
                'count':     int(row['count']),
            })

        # 24시간 분포 (07→06 순서 유지)
        max_avg = hourly['avg_range'].max() if len(hourly) > 0 else 0
        distribution = []
        for _, row in hourly.iterrows():
            ratio = (row['avg_range'] / max_avg) if max_avg > 0 else 0
            distribution.append({
                'hour':      int(row['hour']),
                'avg_range': float(row['avg_range']),
                'ratio':     float(ratio),
                'count':     int(row['count']),
            })

        covered_hours = int((hourly['avg_range'] > 0).sum())

        return {
            '_diag': {
                'kst_first':       str(kst_first),
                'kst_last':        str(kst_last),
                'target_date':     str(target_date),
                'day_start':       str(day_start),
                'day_end':         str(day_end),
                'matched_candles': int(day_df.shape[0]),
                'covered_hours':   covered_hours,
                'tz_offset_used':  source_tz_offset_hours,
                'tz_aware':        is_tz_aware,
            },
            'target_date':   target_date.strftime('%Y-%m-%d'),
            'total_candles': int(day_df.shape[0]),
            'top':           top,
            'distribution':  distribution,
        }


    # --------------------------------
    # MT5 서버 시간대 자동 추정
    # --------------------------------
    @staticmethod
    def estimate_mt5_offset_hours(
        server_time_unix: int,
        local_utc_unix: float,
    ) -> float:
        try:
            diff_hours = (server_time_unix - local_utc_unix) / 3600.0
            return float(round(diff_hours))
        except Exception:
            return 2.0
