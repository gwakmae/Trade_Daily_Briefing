# core/report_formatter.py
# ReportBuilder 전용 포맷팅 헬퍼

from config import DECIMAL_PLACES, CANDLE_THRESHOLDS


class ReportFormatter:
    """ReportBuilder 의 포맷팅 / 스타일 판정 유틸리티"""

    def __init__(self):
        self.rw  = CANDLE_THRESHOLDS["reversal_wick"]
        self.rb  = CANDLE_THRESHOLDS["reversal_body"]
        self.eb  = CANDLE_THRESHOLDS["expansion_body"]
        self.ew  = CANDLE_THRESHOLDS["expansion_wick"]
        self.slb = CANDLE_THRESHOLDS["swing_lookback"]

    # ── 값 포맷 ──
    def fmt(self, val, display_name: str) -> str:
        dec = DECIMAL_PLACES.get(display_name, 5)
        return f"{val:,.0f}" if dec == 0 else f"{val:,.{dec}f}"

    # ── 방향 HTML ──
    def direction_html(self, d: str) -> str:
        if d == 'up':
            return '<span class="up">↑ 상승</span>'
        return '<span class="dn">↓ 하락</span>'

    # ── 위꼬리/아래꼬리 강조 스타일 ──
    def wick_style(self, pct: float) -> str:
        if pct >= self.rw:
            return 'color:#c0392b;font-weight:bold'
        elif pct >= 25:
            return 'color:#d35400;font-weight:bold'
        return ''

    # ── 몸통 강조 스타일 ──
    def body_style(self, pct: float) -> str:
        if pct >= self.eb:
            return 'color:#1e8449;font-weight:bold'
        return ''

    # ── 스윙 HTML ──
    def swing_html(self, sh: bool, sl: bool) -> str:
        r = []
        if sh:
            r.append('<span class="badge badge-swing-h">SwH</span>')
        if sl:
            r.append('<span class="badge badge-swing-l">SwL</span>')
        return ' '.join(r) if r else '-'

    # ── 캔들 번호 배지 ──
    def candle_num_html(self, cn: str) -> str:
        colors = {'C2': '#c0392b', 'C3': '#d35400', 'C4': '#1e8449'}
        if cn in colors:
            return (
                f'<span class="badge" '
                f'style="background:{colors[cn]}">{cn}</span>'
            )
        return '<span style="color:#aaa">-</span>'

    # ── 캔들 유형 레이블 ──
    @staticmethod
    def candle_type_label(ct: str) -> str:
        return {
            'reversal_upper': '반전(위꼬리)',
            'reversal_lower': '반전(아래꼬리)',
            'expansion':      '확장',
            'neutral':        '-'
        }.get(ct, '-')

    # ── 앵커 ID ──
    @staticmethod
    def anchor_id(display_name: str) -> str:
        return "card-" + "".join(
            c if c.isalnum() else "_" for c in display_name
        )