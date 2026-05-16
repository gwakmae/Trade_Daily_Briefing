# core/rth_org_formatter.py
# 브리핑 텍스트 요약 포맷팅

from core.rth_org_config import RTH_ORG_SYMBOLS
from core.rth_org_analyzer import classify_gap


def format_gap_summary(symbol: str, gap_info: dict | None, fill_info: dict | None = None) -> str:
    """당일 갭 텍스트 요약 (브리핑 출력용)"""
    if gap_info is None:
        return f"[{symbol}] RTH ORG 갭 데이터 없음"

    cfg       = RTH_ORG_SYMBOLS.get(symbol, RTH_ORG_SYMBOLS["US100"])
    dec       = cfg["decimals"]
    gap_abs   = gap_info["gap_abs"]
    gap_dir   = gap_info["gap_dir"]
    dir_arrow = "▲ UP" if gap_dir == "UP" else "▼ DOWN"

    size_info  = classify_gap(symbol, gap_abs)
    size_label = size_info["size_label"]
    f50_pct    = size_info["fill_50_pct"]
    f100_pct   = size_info["fill_100_pct"]

    if gap_dir == "UP":
        dir_f50  = cfg["up_fill_50"]
        dir_f100 = cfg["up_fill_100"]
    else:
        dir_f50  = cfg["down_fill_50"]
        dir_f100 = cfg["down_fill_100"]

    fill_status_str = ""
    if fill_info:
        status = fill_info.get("fill_status", "")
        if status == "FILLED_100":
            fill_status_str = " ✅ 100% 채움"
        elif status == "FILLED_50":
            fill_status_str = " 🟡 50% 채움"
        else:
            fill_status_str = " 🔴 미채움"

    lines = [
        f"[RTH ORG — {symbol}]{fill_status_str}",
        f"  전일 RTH Close : {gap_info['rth_close']:,.{dec}f}  ({gap_info['rth_close_time'].strftime('%m/%d %H:%M')} 서버)",
        f"  당일 RTH Open  : {gap_info['rth_open']:,.{dec}f}  ({gap_info['rth_open_time'].strftime('%m/%d %H:%M')} 서버)",
        f"  갭 방향        : {dir_arrow}  {gap_info['gap']:+,.{dec}f}pt  ({size_label})",
        f"  Gap High       : {gap_info['gap_high']:,.{dec}f}  ← {'저항(진입 위)' if gap_dir == 'UP' else '채움 목표'}",
        f"  Gap 50%        : {gap_info['gap_50']:,.{dec}f}  ← 핵심 레벨",
        f"  Gap Low        : {gap_info['gap_low']:,.{dec}f}  ← {'채움 목표' if gap_dir == 'UP' else '지지(진입 아래)'}",
        f"  채움 확률(크기): 50%={f50_pct:.0f}%  /  100%={f100_pct:.0f}%",
        f"  채움 확률(방향): 50%={dir_f50:.0f}%  /  100%={dir_f100:.0f}%",
    ]
    return "\n".join(lines)