# core/rth_org_analyzer.py
# RTH ORG 핵심 계산 및 갭 분석 로직
#
# 주요 변경:
#   - calc_gap_for_date / check_gap_fill 가 symbol_cfg 를 받음
#   - HK50 런치브레이크 구간 자동 제외
#   - KS200 야간 세션 단독 채움 분석 추가

import pandas as pd
from datetime import date

from core.rth_org_config import RTH_ORG_SYMBOLS
from core.rth_org_utils import (
    get_rth_server_times,
    get_lunch_server_times,
    get_night_server_times,
    to_pts,
)


# ──────────────────────────────────────────────
# 갭 크기 분류
# ──────────────────────────────────────────────
def classify_gap(symbol: str, gap_abs: float) -> dict:
    cfg    = RTH_ORG_SYMBOLS.get(symbol, RTH_ORG_SYMBOLS["US100"])
    bins   = cfg["size_bins"]
    labels = cfg["size_labels"]
    stats  = cfg["fill_stats"]

    size_label = labels[-1]
    for i in range(len(bins) - 1):
        if bins[i] <= gap_abs < bins[i + 1]:
            size_label = labels[i]
            break

    fill_stat = stats.get(size_label, {"fill_50": 0.0, "fill_100": 0.0})
    return {
        "size_label":   size_label,
        "fill_50_pct":  fill_stat["fill_50"],
        "fill_100_pct": fill_stat["fill_100"],
    }


# ──────────────────────────────────────────────
# 특정 날짜의 갭 계산
# ──────────────────────────────────────────────
def calc_gap_for_date(df: pd.DataFrame, symbol: str,
                      target_date: date) -> dict | None:
    cfg = RTH_ORG_SYMBOLS.get(symbol)
    if cfg is None:
        return None

    dates = sorted(df["date"].unique())

    try:
        today_idx = list(dates).index(target_date)
    except ValueError:
        return None

    if today_idx == 0:
        return None

    prev_date = dates[today_idx - 1]

    _, close_time = get_rth_server_times(prev_date, cfg)
    open_time, _  = get_rth_server_times(target_date, cfg)

    close_pts = to_pts(close_time)
    open_pts  = to_pts(open_time)

    # ±5분 윈도우 내에서 가장 가까운 봉
    close_candle = df[
        (df["server_time"] >= close_pts - pd.Timedelta(minutes=5)) &
        (df["server_time"] <= close_pts + pd.Timedelta(minutes=5))
    ]
    open_candle = df[
        (df["server_time"] >= open_pts - pd.Timedelta(minutes=5)) &
        (df["server_time"] <= open_pts + pd.Timedelta(minutes=5))
    ]

    if close_candle.empty or open_candle.empty:
        return None

    ci = (close_candle["server_time"] - close_pts).abs().idxmin()
    oi = (open_candle["server_time"]  - open_pts ).abs().idxmin()

    rth_close = float(close_candle.loc[ci, "close"])
    rth_open  = float(open_candle.loc[oi, "open"])

    gap      = rth_open - rth_close
    gap_abs  = abs(gap)
    gap_dir  = "UP" if gap > 0 else "DOWN"
    gap_high = max(rth_close, rth_open)
    gap_low  = min(rth_close, rth_open)
    gap_50   = (gap_high + gap_low) / 2

    return {
        "symbol":         symbol,
        "date":           target_date,
        "rth_close_time": close_time,
        "rth_open_time":  open_time,
        "rth_close":      rth_close,
        "rth_open":       rth_open,
        "gap":            gap,
        "gap_abs":        gap_abs,
        "gap_dir":        gap_dir,
        "gap_high":       gap_high,
        "gap_low":        gap_low,
        "gap_50":         gap_50,
    }


# ──────────────────────────────────────────────
# 갭 채움 여부 확인 (정규장 세션)
# 런치브레이크 구간은 자동으로 제외
# ──────────────────────────────────────────────
def check_gap_fill(df: pd.DataFrame, symbol: str,
                   gap_info: dict) -> dict:
    cfg = RTH_ORG_SYMBOLS.get(symbol)
    if cfg is None:
        return {"fill_50": None, "fill_100": None,
                "fill_status": "NO_CFG", "note": "no_symbol_cfg"}

    d        = gap_info["date"]
    gap_dir  = gap_info["gap_dir"]
    gap_high = gap_info["gap_high"]
    gap_low  = gap_info["gap_low"]
    gap_50   = gap_info["gap_50"]

    open_time, close_time = get_rth_server_times(d, cfg)
    open_pts  = to_pts(open_time)
    close_pts = to_pts(close_time)

    rth_candles = df[
        (df["server_time"] >= open_pts) &
        (df["server_time"] <= close_pts)
    ].copy()

    # 런치브레이크 제외
    lunch_s, lunch_e = get_lunch_server_times(d, cfg)
    if lunch_s is not None and lunch_e is not None:
        ls = to_pts(lunch_s)
        le = to_pts(lunch_e)
        rth_candles = rth_candles[
            ~((rth_candles["server_time"] >= ls) &
              (rth_candles["server_time"] <  le))
        ]

    if rth_candles.empty:
        return {"fill_50": None, "fill_100": None,
                "fill_status": "NO_DATA", "note": "no_rth_data"}

    session_high = rth_candles["high"].max()
    session_low  = rth_candles["low"].min()

    if gap_dir == "UP":
        fill_50  = bool(session_low  <= gap_50)
        fill_100 = bool(session_low  <= gap_low)
    else:
        fill_50  = bool(session_high >= gap_50)
        fill_100 = bool(session_high >= gap_high)

    if fill_100:
        status = "FILLED_100"
    elif fill_50:
        status = "FILLED_50"
    else:
        status = "NOT_FILLED"

    return {
        "fill_50":     fill_50,
        "fill_100":    fill_100,
        "fill_status": status,
        "note":        "",
    }


# ──────────────────────────────────────────────
# 야간 세션 단독 채움 (KS200 등)
# ──────────────────────────────────────────────
def check_night_gap_fill(df: pd.DataFrame, symbol: str,
                         gap_info: dict) -> dict | None:
    cfg = RTH_ORG_SYMBOLS.get(symbol)
    if cfg is None or cfg.get("night") is None:
        return None

    d        = gap_info["date"]
    gap_dir  = gap_info["gap_dir"]
    gap_high = gap_info["gap_high"]
    gap_low  = gap_info["gap_low"]
    gap_50   = gap_info["gap_50"]

    night_s, night_e = get_night_server_times(d, cfg)
    if night_s is None:
        return None

    s_pts = to_pts(night_s)
    e_pts = to_pts(night_e)

    night_candles = df[
        (df["server_time"] >= s_pts) &
        (df["server_time"] <  e_pts)
    ]

    if night_candles.empty:
        return None

    n_high = night_candles["high"].max()
    n_low  = night_candles["low"].min()

    if gap_dir == "UP":
        fill_50  = bool(n_low  <= gap_50)
        fill_100 = bool(n_low  <= gap_low)
    else:
        fill_50  = bool(n_high >= gap_50)
        fill_100 = bool(n_high >= gap_high)

    return {
        "night_fill_50":  fill_50,
        "night_fill_100": fill_100,
    }


# ──────────────────────────────────────────────
# 과거 N일치 갭 레벨 수집
# ──────────────────────────────────────────────
def get_historical_gaps(df: pd.DataFrame, symbol: str,
                        days: int = 10) -> list[dict]:
    cfg     = RTH_ORG_SYMBOLS.get(symbol)
    if cfg is None:
        return []

    min_gap = cfg["min_gap"]
    dec     = cfg["decimals"]

    dates       = sorted(df["date"].unique())
    check_dates = dates[-(days + 2):]
    results     = []

    for i in range(1, len(check_dates)):
        target_date = check_dates[i]
        gap_info    = calc_gap_for_date(df, symbol, target_date)

        if gap_info is None:
            continue

        gap_abs = gap_info["gap_abs"]

        if gap_abs < min_gap:
            gap_info["note"]        = "gap_too_small"
            gap_info["fill_status"] = "TOO_SMALL"
            gap_info["fill_50"]     = None
            gap_info["fill_100"]    = None
        else:
            fill_info = check_gap_fill(df, symbol, gap_info)
            gap_info.update(fill_info)

            night_info = check_night_gap_fill(df, symbol, gap_info)
            if night_info is not None:
                gap_info.update(night_info)

        size_info = classify_gap(symbol, gap_abs)
        gap_info.update(size_info)

        for key in ["rth_close", "rth_open", "gap",
                    "gap_abs", "gap_high", "gap_low", "gap_50"]:
            if key in gap_info and gap_info[key] is not None:
                gap_info[key] = round(float(gap_info[key]), dec)

        results.append(gap_info)

    return list(reversed(results[-days:]))


# ──────────────────────────────────────────────
# 미채움 갭 레벨 필터 (지지/저항 레벨)
# ──────────────────────────────────────────────
def get_unfilled_gap_levels(historical_gaps: list[dict],
                            current_price: float | None = None) -> dict:
    above = []
    below = []

    for g in historical_gaps:
        status = g.get("fill_status", "")

        if status in ("FILLED_100", "TOO_SMALL", "NO_DATA"):
            continue

        level_info = {
            "date":     g["date"].strftime("%m/%d")
                        if hasattr(g["date"], "strftime")
                        else str(g["date"]),
            "gap_dir":  g["gap_dir"],
            "gap_high": g["gap_high"],
            "gap_low":  g["gap_low"],
            "gap_50":   g["gap_50"],
            "status":   status,
        }

        if current_price is None:
            above.append(level_info)
        else:
            center = (g["gap_high"] + g["gap_low"]) / 2
            if center > current_price:
                above.append(level_info)
            else:
                below.append(level_info)

    above.sort(key=lambda x: x["gap_low"])
    below.sort(key=lambda x: x["gap_high"], reverse=True)

    return {"resistance": above, "support": below}
