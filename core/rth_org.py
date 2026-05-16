# core/rth_org.py
# RTH ORG 분석 모듈 메인 실행부 (Facade)
#
# 변경 사항:
#   - 브로커별 자동 그룹핑 지원
#   - 다중 심볼 (US100, US500, KS200, HK50) 동시 처리
#   - target_date 가 None 이면 데이터 마지막 날짜 사용

import MetaTrader5 as mt5
from datetime import date

from config import BROKERS
from core.rth_org_config import (
    RTH_ORG_SYMBOLS,
    DEFAULT_BROKER_BY_SYMBOL,
)
from core.rth_org_utils import fetch_m5_data
from core.rth_org_analyzer import (
    calc_gap_for_date,
    check_gap_fill,
    check_night_gap_fill,
    get_historical_gaps,
    get_unfilled_gap_levels,
)
from core.rth_org_formatter import format_gap_summary


# ──────────────────────────────────────────────
# 단일 브로커 세션에서 여러 심볼 분석
# ──────────────────────────────────────────────
def _analyze_for_broker(
    broker_name: str,
    symbols: list[str],
    days: int,
    target_date: date | None,
) -> dict:
    broker_cfg = BROKERS.get(broker_name, {})

    if not mt5.initialize(path=broker_cfg.get("path", "")):
        raise RuntimeError(
            f"[{broker_name}] MT5 초기화 실패: {mt5.last_error()}"
        )

    if not mt5.login(
        broker_cfg.get("login", 0),
        broker_cfg.get("password", ""),
        broker_cfg.get("server", ""),
    ):
        mt5.shutdown()
        raise RuntimeError(
            f"[{broker_name}] MT5 로그인 실패: {mt5.last_error()}"
        )

    results = {}

    try:
        for symbol in symbols:
            cfg = RTH_ORG_SYMBOLS.get(symbol)
            if cfg is None:
                results[symbol] = None
                continue

            df = fetch_m5_data(symbol)
            if df is None or len(df) == 0:
                results[symbol] = None
                continue

            # 분석 기준일 결정
            if target_date is not None:
                t_date = target_date
            else:
                dates  = sorted(df["date"].unique())
                t_date = dates[-1]

            today_gap        = calc_gap_for_date(df, symbol, t_date)
            today_fill       = None
            today_night_fill = None

            if today_gap and today_gap.get("gap_abs", 0) >= cfg["min_gap"]:
                today_fill = check_gap_fill(df, symbol, today_gap)

                if cfg.get("night") is not None:
                    today_night_fill = check_night_gap_fill(
                        df, symbol, today_gap
                    )

                summary = format_gap_summary(symbol, today_gap, today_fill)
            else:
                summary = format_gap_summary(symbol, today_gap)

            historical_gaps = get_historical_gaps(df, symbol, days)

            # 현재가: 마지막 봉의 close
            current_price = float(df["close"].iloc[-1])
            unfilled_levels = get_unfilled_gap_levels(
                historical_gaps, current_price
            )

            results[symbol] = {
                "symbol":            symbol,
                "broker":            broker_name,
                "today_gap":         today_gap,
                "today_fill":        today_fill,
                "today_night_fill":  today_night_fill,
                "historical_gaps":   historical_gaps,
                "unfilled_levels":   unfilled_levels,
                "summary_text":      summary,
                "current_price":     current_price,
                "df":                df,
            }

    finally:
        mt5.shutdown()

    return results


# ──────────────────────────────────────────────
# 메인 진입점
# 심볼 → 브로커 자동 매핑 후 그룹별로 분석
# ──────────────────────────────────────────────
def run_rth_org_analysis(
    broker_name: str | None = None,
    symbols: list[str] | None = None,
    days: int = 10,
    target_date: date | None = None,
) -> dict:
    """
    아침 브리핑용 통합 진입점.

    - broker_name=None : 심볼별 DEFAULT_BROKER_BY_SYMBOL 매핑 사용
    - broker_name 지정 : 모든 심볼을 그 브로커에서 가져옴

    반환: {symbol: result_dict, ...}
    """
    if symbols is None:
        symbols = ["US100", "US500", "KS200", "HK50"]

    # 브로커별 그룹핑
    groups: dict[str, list[str]] = {}

    for sym in symbols:
        bn = broker_name or DEFAULT_BROKER_BY_SYMBOL.get(sym, "FP Markets")
        groups.setdefault(bn, []).append(sym)

    all_results: dict = {}

    for bn, syms in groups.items():
        try:
            partial = _analyze_for_broker(bn, syms, days, target_date)
            all_results.update(partial)
        except Exception as e:
            for s in syms:
                all_results[s] = {
                    "symbol":      s,
                    "broker":      bn,
                    "error":       str(e),
                    "today_gap":   None,
                    "today_fill":  None,
                }

    return all_results
