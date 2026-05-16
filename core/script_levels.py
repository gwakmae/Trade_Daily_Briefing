# core/script_levels.py
# ScriptBuilder 의 레벨 수집 로직 분리

from datetime import date

from config import DECIMAL_PLACES
from core.mt5_connector import MT5Connector


class ScriptLevelCollector:
    """일봉 + 주봉 데이터를 기반으로 MQL5 레벨 목록 수집"""

    def collect(
        self,
        display_name: str,
        yesterday,
        prev1,
        prev2,
        cnum: str,
        direction: str,
        dec: int,
        weekly_df=None,
        manual_date: date = None,
    ) -> list[dict]:
        """레벨 정보를 dict 리스트로 반환"""
        levels = []

        def f(v):
            return f"{v:.{dec}f}"

        def add(name, value, color, style=0, width=1, label="", group="daily"):
            levels.append({
                "name":  name,
                "value": value,
                "color": color,
                "style": style,
                "width": width,
                "label": label if label else name,
                "group": group,
            })

        # ── 일봉 공통 레벨 ──
        add("PrevHigh", yesterday['high'], "clrRed",
            label=f"PrevHigh : {f(yesterday['high'])}")
        add("PrevLow", yesterday['low'], "clrRoyalBlue",
            label=f"PrevLow : {f(yesterday['low'])}")
        add("PrevOpen", yesterday['open'], "clrGray", style=2,
            label=f"PrevOpen : {f(yesterday['open'])}")
        add("PrevClose", yesterday['close'], "clrDimGray", style=2,
            label=f"PrevClose : {f(yesterday['close'])}")
        add("PrevEQ", yesterday['eq'], "clrDarkOrange", style=1, width=2,
            label=f"PrevEQ(0.5) : {f(yesterday['eq'])}")

        # ── C3 핵심 기준선 ──
        if cnum == 'C3':
            add("C3_EQ_Key", yesterday['eq'], "clrMagenta", width=2,
                label=f"C3_EQ_Key : {f(yesterday['eq'])}")

        # ── C4 레벨 ──
        elif cnum == 'C4':
            c3_eq        = prev2['eq']
            c3_high      = prev2['high']
            c3_low       = prev2['low']
            c3_upper_mid = (c3_high + c3_eq) / 2
            c3_lower_mid = (c3_eq + c3_low) / 2

            add("C3_High", c3_high, "clrLightCoral", style=2,
                label=f"C3_High : {f(c3_high)}")
            add("C3_Low", c3_low, "clrLightBlue", style=2,
                label=f"C3_Low : {f(c3_low)}")
            add("C3_EQ", c3_eq, "clrMagenta", width=2,
                label=f"C3_EQ : {f(c3_eq)}")

            if direction == 'up':
                add("C3_UpperMid", c3_upper_mid, "clrLimeGreen", style=1,
                    label=f"C3_UpperMid : {f(c3_upper_mid)}")
            else:
                add("C3_LowerMid", c3_lower_mid, "clrOrangeRed", style=1,
                    label=f"C3_LowerMid : {f(c3_lower_mid)}")

        # ── 전주봉 레벨 ──
        if weekly_df is not None and len(weekly_df) >= 3:
            try:
                w_idx = MT5Connector.get_last_week_idx(
                    weekly_df, reference_date=manual_date
                )
                w = weekly_df.iloc[w_idx]

                w_high  = float(w['high'])
                w_low   = float(w['low'])
                w_open  = float(w['open'])
                w_close = float(w['close'])

                if 'eq' in weekly_df.columns:
                    w_eq = float(w['eq'])
                else:
                    w_eq = (w_high + w_low) / 2

                add("LastWeekHigh", w_high, "clrPurple", width=2,
                    label=f"W High : {f(w_high)}", group="weekly")
                add("LastWeekLow", w_low, "clrDodgerBlue", width=2,
                    label=f"W Low : {f(w_low)}", group="weekly")
                add("LastWeekOpen", w_open, "clrGray", style=2,
                    label=f"W Open : {f(w_open)}", group="weekly")
                add("LastWeekClose", w_close, "clrDimGray", style=2,
                    label=f"W Close : {f(w_close)}", group="weekly")
                add("LastWeekEQ", w_eq, "clrGold", style=1, width=2,
                    label=f"W EQ(0.5) : {f(w_eq)}", group="weekly")

            except Exception as e:
                print(f"[ScriptLevelCollector] 주봉 레벨 생성 실패: {display_name} / {e}")

        return levels