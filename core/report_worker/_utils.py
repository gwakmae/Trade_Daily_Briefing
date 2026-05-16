import pandas as pd
from datetime import date

INTRADAY_M5_COUNT = 4000

def resample_to_hourly(
    m5_df: pd.DataFrame,
    target_kst_date: date,
    server_offset: float = 0.0,
) -> list[dict] | None:
    """
    5분봉 DataFrame → 1시간봉 OHLC 리스트 변환
    거래일 정의: KST 07:00 ~ 익일 KST 06:59
    """
    if m5_df is None or m5_df.empty:
        return None
    df = m5_df.copy()
    if 'date' in df.columns:
        df = df.set_index('date')

    # 인덱스를 KST로 통일
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        df.index = df.index.tz_convert('Asia/Seoul')
    else:
        kst_shift_hours = 9.0 - server_offset
        df.index = df.index + pd.Timedelta(hours=kst_shift_hours)

    # 거래일 기준 필터링
    day_start = pd.Timestamp(target_kst_date) + pd.Timedelta(hours=7)
    day_end   = day_start + pd.Timedelta(days=1)
    if hasattr(df.index, 'tz') and df.index.tz is not None:
        day_start = day_start.tz_localize('Asia/Seoul')
        day_end   = day_end.tz_localize('Asia/Seoul')
    df = df[(df.index >= day_start) & (df.index < day_end)]
    if df.empty:
        return None

    # 1시간 단위 resample
    hourly = df.resample('1h').agg(
        open=('open', 'first'),
        high=('high', 'max'),
        low=('low', 'min'),
        close=('close', 'last'),
    ).dropna(subset=['open', 'close'])
    if hourly.empty:
        return None

    # dict 리스트로 변환
    result = []
    for ts, row in hourly.iterrows():
        result.append({
            'hour': ts.hour,
            'open': float(row['open']),
            'high': float(row['high']),
            'low':  float(row['low']),
            'close': float(row['close']),
        })
    return result if result else None