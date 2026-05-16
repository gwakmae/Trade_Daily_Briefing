# core/rth_org_utils.py
# RTH ORG 시간 계산 및 데이터 수집 유틸리티
#
# 변경 사항:
#   - get_rth_server_times() 가 symbol_cfg 를 받아 일반화됨
#   - HK50 런치브레이크 / KS200 야간세션 시간 계산 헬퍼 추가

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

from core.rth_org_config import SERVER_TZ


# ──────────────────────────────────────────────
# 미국 DST 판단
# 3월 둘째 일요일 ~ 11월 첫째 일요일
# ──────────────────────────────────────────────
def is_us_dst(d) -> bool:
    if isinstance(d, datetime):
        d = d.date()

    march1      = datetime(d.year, 3, 1)
    days_to_sun = (6 - march1.weekday()) % 7
    dst_start   = (march1 + timedelta(days=days_to_sun + 7)).date()

    nov1        = datetime(d.year, 11, 1)
    days_to_sun = (6 - nov1.weekday()) % 7
    dst_end     = (nov1 + timedelta(days=days_to_sun)).date()

    return dst_start <= d < dst_end


# ──────────────────────────────────────────────
# RTH Open / Close 서버 시간 반환 (심볼별)
# ──────────────────────────────────────────────
def get_rth_server_times(d, symbol_cfg: dict, tz=SERVER_TZ):
    """
    symbol_cfg : RTH_ORG_SYMBOLS[symbol]
    반환       : (rth_open_dt, rth_close_dt)
    """
    if isinstance(d, datetime):
        d = d.date()

    open_h,  open_m  = symbol_cfg["rth_open"]
    close_h, close_m = symbol_cfg["rth_close"]

    # 미국 DST 보정 (비DST 시 +1시간)
    if symbol_cfg.get("dst_aware") and not is_us_dst(d):
        open_h  += 1
        close_h += 1

    rth_open = datetime(
        d.year, d.month, d.day, open_h, open_m, tzinfo=tz
    )

    # close 가 24시 이상 → 익일로
    if close_h >= 24:
        next_day  = d + timedelta(days=1)
        rth_close = datetime(
            next_day.year, next_day.month, next_day.day,
            close_h - 24, close_m, tzinfo=tz
        )
    else:
        rth_close = datetime(
            d.year, d.month, d.day, close_h, close_m, tzinfo=tz
        )

    return rth_open, rth_close


# ──────────────────────────────────────────────
# 런치브레이크 서버 시간 반환 (HK50 등)
# ──────────────────────────────────────────────
def get_lunch_server_times(d, symbol_cfg: dict, tz=SERVER_TZ):
    if symbol_cfg.get("lunch") is None:
        return None, None

    if isinstance(d, datetime):
        d = d.date()

    (s_h, s_m), (e_h, e_m) = symbol_cfg["lunch"]

    lunch_start = datetime(d.year, d.month, d.day, s_h, s_m, tzinfo=tz)
    lunch_end   = datetime(d.year, d.month, d.day, e_h, e_m, tzinfo=tz)
    return lunch_start, lunch_end


# ──────────────────────────────────────────────
# 야간 세션 서버 시간 반환 (KS200 등)
# 종료 시각이 24시 이상이면 익일
# ──────────────────────────────────────────────
def get_night_server_times(d, symbol_cfg: dict, tz=SERVER_TZ):
    if symbol_cfg.get("night") is None:
        return None, None

    if isinstance(d, datetime):
        d = d.date()

    (s_h, s_m), (e_h, e_m) = symbol_cfg["night"]

    night_start = datetime(d.year, d.month, d.day, s_h, s_m, tzinfo=tz)

    if e_h >= 24:
        next_day  = d + timedelta(days=1)
        night_end = datetime(
            next_day.year, next_day.month, next_day.day,
            e_h - 24, e_m, tzinfo=tz
        )
    else:
        night_end = datetime(d.year, d.month, d.day, e_h, e_m, tzinfo=tz)

    return night_start, night_end


# ──────────────────────────────────────────────
# pd.Timestamp 변환 헬퍼
# ──────────────────────────────────────────────
def to_pts(dt) -> pd.Timestamp:
    return pd.Timestamp(dt).tz_convert("Etc/GMT-3")


# ──────────────────────────────────────────────
# MT5 5분봉 데이터 수집 (연결된 상태에서 호출)
# ──────────────────────────────────────────────
def fetch_m5_data(symbol: str, count: int = 50000) -> pd.DataFrame | None:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    if rates is None or len(rates) == 0:
        return None

    df = pd.DataFrame(rates)
    df["time"]        = pd.to_datetime(df["time"], unit="s", utc=True)
    df["server_time"] = df["time"].dt.tz_convert("Etc/GMT-3")
    df = df[["server_time", "open", "high", "low", "close"]].copy()
    df["date"] = df["server_time"].dt.date
    return df
