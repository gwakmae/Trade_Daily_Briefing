from config import DECIMAL_PLACES


class ChartComponents:
    # ──────────────────────────────────────────────────────────────
    # 전일 1시간봉 — 캔들 + 파동을 세로로 분리, 각자 카드 풀폭
    # ──────────────────────────────────────────────────────────────
    def hourly_chart_html(self, hourly_data: list[dict] | None,
                          display_name: str) -> str:
        if not hourly_data:
            return """
<div class="hourly-chart-wrap hourly-chart-empty">
  <div class="hourly-chart-title">🕐 전일 1시간봉</div>
  <div class="hourly-empty-msg">5분봉 데이터 없음</div>
</div>"""

        n = len(hourly_data)
        if n == 0:
            return ""

        dec = DECIMAL_PLACES.get(display_name, 5)

        def fmt_p(v):
            return f"{v:,.{dec}f}" if dec > 0 else f"{v:,.0f}"

        SESSION_COLORS = {
            'asia':   '#1e3a5f',
            'europe': '#2d1b4e',
            'ny':     '#3b1f0a',
        }
        SESSION_LABELS = {
            'asia':   ('AS', '#3b82f6'),
            'europe': ('EU', '#8b5cf6'),
            'ny':     ('NY', '#f97316'),
        }

        def get_session(hour: int) -> str:
            if 7 <= hour <= 15:
                return 'asia'
            elif 16 <= hour <= 21:
                return 'europe'
            else:
                return 'ny'

        # 세션 블록 (인덱스 기반)
        session_blocks_idx = []
        cur_sess, block_start = get_session(hourly_data[0]['hour']), 0
        for i, c in enumerate(hourly_data):
            sess = get_session(c['hour'])
            if sess != cur_sess or i == n - 1:
                end_i = i if sess != cur_sess else i + 1
                session_blocks_idx.append((cur_sess, block_start, end_i))
                cur_sess, block_start = sess, i

        legend_html = " &nbsp; ".join([
            '<span class="hc-sess-as">■</span> 아시아(07~15 KST)',
            '<span class="hc-sess-eu">■</span> 유럽(16~21 KST)',
            '<span class="hc-sess-ny">■</span> 뉴욕(22~06 KST)',
        ])

        candle_svg = self._build_hourly_candle_svg(
            hourly_data, n, fmt_p,
            session_blocks_idx, SESSION_COLORS, SESSION_LABELS, get_session,
        )
        wave_svg = self._build_hourly_wave_svg(
            hourly_data, n, fmt_p,
            session_blocks_idx, SESSION_COLORS, SESSION_LABELS, get_session,
        )

        return f"""
<div class="hourly-chart-stack">
  <div class="hourly-chart-wrap">
    <div class="hourly-chart-title">
      🕐 전일 1시간봉 캔들
      <span class="hourly-chart-sub">KST · {n}봉</span>
      <span class="hourly-chart-legend">{legend_html}</span>
    </div>
    <div class="hourly-svg-scroll">{candle_svg}</div>
  </div>
  <div class="hourly-chart-wrap">
    <div class="hourly-chart-title">
      🌊 전일 1시간봉 파동 (Close)
      <span class="hourly-chart-sub">KST · {n}점</span>
    </div>
    <div class="hourly-svg-scroll">{wave_svg}</div>
  </div>
</div>"""

    # ──────────────────────────────────────────────────────────────
    # 1시간봉 캔들 SVG (viewBox 기반, CSS width:100% 로 늘어남)
    # ──────────────────────────────────────────────────────────────
    def _build_hourly_candle_svg(
        self, hourly_data, n, fmt_p,
        session_blocks_idx, SESSION_COLORS, SESSION_LABELS, get_session,
    ) -> str:
        # 내부 좌표계 (viewBox 기준 단위)
        CANDLE_W = 28
        GAP      = 10
        LEFT_PAD = 64
        RIGHT_PAD = 16
        TOP_PAD  = 28
        BOT_PAD  = 32
        CHART_H  = 180

        SVG_W = LEFT_PAD + n * (CANDLE_W + GAP) - GAP + RIGHT_PAD
        SVG_H = TOP_PAD + CHART_H + BOT_PAD

        all_highs = [c['high'] for c in hourly_data]
        all_lows  = [c['low']  for c in hourly_data]
        price_max = max(all_highs)
        price_min = min(all_lows)
        price_rng = price_max - price_min if price_max != price_min else 1.0

        def to_y(price):
            ratio = (price_max - price) / price_rng
            return TOP_PAD + ratio * CHART_H

        max_idx = all_highs.index(price_max)
        min_idx = all_lows.index(price_min)

        elements = [f'<rect x="0" y="0" width="{SVG_W}" height="{SVG_H}" rx="6" fill="#0f172a"/>']

        # 세션 배경
        for sess, si, ei in session_blocks_idx:
            x1 = LEFT_PAD + si * (CANDLE_W + GAP) - GAP / 2
            x2 = LEFT_PAD + ei * (CANDLE_W + GAP) - GAP / 2
            elements.append(
                f'<rect x="{x1:.1f}" y="{TOP_PAD}" width="{x2 - x1:.1f}" '
                f'height="{CHART_H}" fill="{SESSION_COLORS[sess]}" opacity="0.5"/>'
            )

        # 가로 가이드선
        for frac, col in [(0.0, '#1e293b'), (0.5, '#334155'), (1.0, '#1e293b')]:
            gy = TOP_PAD + frac * CHART_H
            elements.append(
                f'<line x1="{LEFT_PAD}" y1="{gy:.1f}" x2="{SVG_W - RIGHT_PAD}" '
                f'y2="{gy:.1f}" stroke="{col}" stroke-width="1"/>'
            )

        # Y축 가격 레이블
        mid_price = (price_max + price_min) / 2
        for price, frac in [(price_max, 0.0), (mid_price, 0.5), (price_min, 1.0)]:
            gy = TOP_PAD + frac * CHART_H
            elements.append(
                f'<text x="{LEFT_PAD - 6}" y="{gy + 3:.1f}" text-anchor="end" '
                f'fill="#94a3b8" font-size="10" font-family="Consolas,monospace">{fmt_p(price)}</text>'
            )

        # 세션 라벨 (위쪽)
        for sess, si, ei in session_blocks_idx:
            x1 = LEFT_PAD + si * (CANDLE_W + GAP) - GAP / 2
            x2 = LEFT_PAD + ei * (CANDLE_W + GAP) - GAP / 2
            label, col = SESSION_LABELS[sess]
            mid_x = (x1 + x2) / 2
            elements.append(
                f'<text x="{mid_x:.1f}" y="{TOP_PAD - 9}" text-anchor="middle" '
                f'fill="{col}" font-size="11" font-weight="bold" '
                f'font-family="Segoe UI,sans-serif">{label}</text>'
            )

        # 캔들
        for i, candle in enumerate(hourly_data):
            cx = LEFT_PAD + i * (CANDLE_W + GAP) + CANDLE_W / 2
            o, h, l, c = candle['open'], candle['high'], candle['low'], candle['close']
            is_bull = c >= o
            color    = "#22c55e" if is_bull else "#ef4444"
            wick_col = "#16a34a" if is_bull else "#dc2626"

            y_open, y_close = to_y(o), to_y(c)
            y_high, y_low   = to_y(h), to_y(l)
            body_top = min(y_open, y_close)
            body_h   = max(abs(y_close - y_open), 1.5)
            candle_x = cx - CANDLE_W / 2

            elements.append(
                f'<line x1="{cx:.1f}" y1="{y_high:.1f}" x2="{cx:.1f}" '
                f'y2="{body_top:.1f}" stroke="{wick_col}" stroke-width="1.8"/>'
            )
            elements.append(
                f'<line x1="{cx:.1f}" y1="{body_top + body_h:.1f}" x2="{cx:.1f}" '
                f'y2="{y_low:.1f}" stroke="{wick_col}" stroke-width="1.8"/>'
            )
            elements.append(
                f'<rect x="{candle_x:.1f}" y="{body_top:.1f}" width="{CANDLE_W}" '
                f'height="{body_h:.1f}" fill="{color}" rx="1.5"/>'
            )

            # 고/저 라벨
            if i == max_idx:
                elements.append(
                    f'<text x="{cx:.1f}" y="{to_y(h) - 6:.1f}" text-anchor="middle" '
                    f'fill="#fbbf24" font-size="10" font-family="Consolas,monospace" '
                    f'font-weight="bold">{fmt_p(h)}</text>'
                )
            if i == min_idx:
                elements.append(
                    f'<text x="{cx:.1f}" y="{to_y(l) + 14:.1f}" text-anchor="middle" '
                    f'fill="#fbbf24" font-size="10" font-family="Consolas,monospace" '
                    f'font-weight="bold">{fmt_p(l)}</text>'
                )

            # X축 시각 라벨 (2열에서는 카드 폭 여유 있으므로 모든 시간 표시)
            hour = candle['hour']
            lbl_col = SESSION_LABELS[get_session(hour)][1]
            elements.append(
                f'<text x="{cx:.1f}" y="{TOP_PAD + CHART_H + 18}" '
                f'text-anchor="middle" fill="{lbl_col}" font-size="10" '
                f'font-family="Consolas,monospace">{hour:02d}</text>'
            )

        svg_body = "\n".join(elements)
        # viewBox 사용 → CSS width:100% 로 컨테이너에 맞춰 늘어남
        return (
            f'<svg viewBox="0 0 {SVG_W} {SVG_H}" '
            f'preserveAspectRatio="xMidYMid meet" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="display:block;border-radius:6px">{svg_body}</svg>'
        )

    # ──────────────────────────────────────────────────────────────
    # 1시간봉 파동 SVG (viewBox 기반)
    # ──────────────────────────────────────────────────────────────
    def _build_hourly_wave_svg(
        self, hourly_data, n, fmt_p,
        session_blocks_idx, SESSION_COLORS, SESSION_LABELS, get_session,
    ) -> str:
        # 캔들 SVG와 동일한 X 좌표계 사용 (수직 정렬을 위해)
        CANDLE_W = 28
        GAP      = 10
        LEFT_PAD = 64
        RIGHT_PAD = 16
        TOP_PAD  = 28
        BOT_PAD  = 32
        CHART_H  = 140

        SVG_W = LEFT_PAD + n * (CANDLE_W + GAP) - GAP + RIGHT_PAD
        SVG_H = TOP_PAD + CHART_H + BOT_PAD

        all_close = [c['close'] for c in hourly_data]
        close_max = max(all_close)
        close_min = min(all_close)
        close_rng = close_max - close_min if close_max != close_min else 1.0

        def to_y(price):
            ratio = (close_max - price) / close_rng
            return TOP_PAD + 8 + ratio * (CHART_H - 16)

        def x_at(i):
            return LEFT_PAD + i * (CANDLE_W + GAP) + CANDLE_W / 2

        elements = [f'<rect x="0" y="0" width="{SVG_W}" height="{SVG_H}" rx="6" fill="#0f172a"/>']

        # 세션 배경
        for sess, si, ei in session_blocks_idx:
            x1 = LEFT_PAD + si * (CANDLE_W + GAP) - GAP / 2
            x2 = LEFT_PAD + ei * (CANDLE_W + GAP) - GAP / 2
            elements.append(
                f'<rect x="{x1:.1f}" y="{TOP_PAD}" width="{x2 - x1:.1f}" '
                f'height="{CHART_H}" fill="{SESSION_COLORS[sess]}" opacity="0.5"/>'
            )

        # 가로 가이드선
        for frac, col in [(0.0, '#1e293b'), (0.5, '#334155'), (1.0, '#1e293b')]:
            gy = TOP_PAD + frac * CHART_H
            elements.append(
                f'<line x1="{LEFT_PAD}" y1="{gy:.1f}" x2="{SVG_W - RIGHT_PAD}" '
                f'y2="{gy:.1f}" stroke="{col}" stroke-width="1"/>'
            )

        # Y축 가격 레이블
        mid_price = (close_max + close_min) / 2
        for price, frac in [(close_max, 0.0), (mid_price, 0.5), (close_min, 1.0)]:
            gy = TOP_PAD + frac * CHART_H
            elements.append(
                f'<text x="{LEFT_PAD - 6}" y="{gy + 3:.1f}" text-anchor="end" '
                f'fill="#94a3b8" font-size="10" font-family="Consolas,monospace">{fmt_p(price)}</text>'
            )

        # 세션 라벨
        for sess, si, ei in session_blocks_idx:
            x1 = LEFT_PAD + si * (CANDLE_W + GAP) - GAP / 2
            x2 = LEFT_PAD + ei * (CANDLE_W + GAP) - GAP / 2
            label, col = SESSION_LABELS[sess]
            mid_x = (x1 + x2) / 2
            elements.append(
                f'<text x="{mid_x:.1f}" y="{TOP_PAD - 9}" text-anchor="middle" '
                f'fill="{col}" font-size="11" font-weight="bold" '
                f'font-family="Segoe UI,sans-serif">{label}</text>'
            )

        # 파동선
        points = [(x_at(i), to_y(c['close']), c) for i, c in enumerate(hourly_data)]
        for i in range(len(points) - 1):
            x1, y1, c1 = points[i]
            x2, y2, c2 = points[i + 1]
            seg_col = "#22c55e" if c2['close'] >= c1['close'] else "#ef4444"
            elements.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{seg_col}" stroke-width="2.5" stroke-linecap="round"/>'
            )

        # 점 + 고/저 강조
        for px, py, candle in points:
            is_high = candle['close'] == close_max
            is_low  = candle['close'] == close_min
            dot_r, dot_col = (4.5, "#fbbf24") if (is_high or is_low) else (2.6, "#cbd5e1")
            elements.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{dot_r}" fill="{dot_col}"/>')

            if is_high:
                elements.append(
                    f'<text x="{px:.1f}" y="{py - 8:.1f}" text-anchor="middle" '
                    f'fill="#fbbf24" font-size="10" font-family="Consolas,monospace" '
                    f'font-weight="bold">{fmt_p(candle["close"])}</text>'
                )
            if is_low:
                elements.append(
                    f'<text x="{px:.1f}" y="{py + 15:.1f}" text-anchor="middle" '
                    f'fill="#fbbf24" font-size="10" font-family="Consolas,monospace" '
                    f'font-weight="bold">{fmt_p(candle["close"])}</text>'
                )

        # X축 시각 라벨
        for i, candle in enumerate(hourly_data):
            hour = candle['hour']
            px = x_at(i)
            lbl_col = SESSION_LABELS[get_session(hour)][1]
            elements.append(
                f'<text x="{px:.1f}" y="{TOP_PAD + CHART_H + 18}" '
                f'text-anchor="middle" fill="{lbl_col}" font-size="10" '
                f'font-family="Consolas,monospace">{hour:02d}</text>'
            )

        svg_body = "\n".join(elements)
        return (
            f'<svg viewBox="0 0 {SVG_W} {SVG_H}" '
            f'preserveAspectRatio="xMidYMid meet" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="display:block;border-radius:6px">{svg_body}</svg>'
        )

    # ──────────────────────────────────────────────────────────────
    # 일봉 미니 캔들차트 (변경 없음 — 카드 우측 280px 박스에서 사용)
    # ──────────────────────────────────────────────────────────────
    def candle_chart_html(self, df, y_idx: int, display_name: str,
                          lookback: int = 4) -> str:
        length, abs_y = len(df), (y_idx if y_idx >= 0 else len(df) + y_idx)
        start, end = max(0, abs_y - lookback + 1), abs_y + 1
        rows = df.iloc[start:end]
        if len(rows) == 0:
            return ""
        n = len(rows)

        SVG_W   = 260
        TOP_PAD = 18
        BOT_PAD = 22
        CHART_H = 130          # ← 카드 좌측 summary 높이와 균형 맞추기 위해 살짝 키움
        SVG_H   = TOP_PAD + CHART_H + BOT_PAD

        CANDLE_W = 28
        GAP      = (SVG_W - n * CANDLE_W) / (n + 1)
        all_highs = [float(r['high']) for _, r in rows.iterrows()]
        all_lows  = [float(r['low'])  for _, r in rows.iterrows()]
        price_max, price_min = max(all_highs), min(all_lows)
        price_rng = price_max - price_min if price_max != price_min else 1.0

        def to_y(price):
            ratio = (price_max - price) / price_rng
            return TOP_PAD + ratio * CHART_H

        elements = [f'<rect x="0" y="0" width="{SVG_W}" height="{SVG_H}" rx="6" fill="#1e293b"/>']
        mid_price = (price_max + price_min) / 2
        mid_y = to_y(mid_price)
        elements.append(
            f'<line x1="0" y1="{mid_y:.1f}" x2="{SVG_W}" y2="{mid_y:.1f}" '
            f'stroke="#334155" stroke-width="1" stroke-dasharray="3,3"/>'
        )

        dec = DECIMAL_PLACES.get(display_name, 5)

        def fmt_price(v):
            return f"{v:,.{dec}f}" if dec > 0 else f"{v:,.0f}"

        elements.append(
            f'<text x="4" y="{TOP_PAD - 3:.1f}" fill="#64748b" font-size="9" '
            f'font-family="Consolas,monospace">{fmt_price(price_max)}</text>'
        )
        elements.append(
            f'<text x="4" y="{TOP_PAD + CHART_H + 1:.1f}" fill="#64748b" font-size="9" '
            f'font-family="Consolas,monospace">{fmt_price(price_min)}</text>'
        )

        for i, (idx, row) in enumerate(rows.iterrows()):
            cx = GAP + i * (CANDLE_W + GAP) + CANDLE_W / 2
            o, h, l, c = float(row['open']), float(row['high']), float(row['low']), float(row['close'])
            is_bull = c >= o
            is_yesterday = (start + i) == abs_y
            color    = "#22c55e" if is_bull else "#ef4444"
            wick_col = "#16a34a" if is_bull else "#dc2626"
            y_open, y_close = to_y(o), to_y(c)
            y_high, y_low   = to_y(h), to_y(l)
            body_top = min(y_open, y_close)
            body_h   = max(abs(y_close - y_open), 1.5)
            candle_x = cx - CANDLE_W / 2
            elements.append(
                f'<line x1="{cx:.1f}" y1="{y_high:.1f}" x2="{cx:.1f}" '
                f'y2="{body_top:.1f}" stroke="{wick_col}" stroke-width="1.6"/>'
            )
            elements.append(
                f'<line x1="{cx:.1f}" y1="{body_top + body_h:.1f}" x2="{cx:.1f}" '
                f'y2="{y_low:.1f}" stroke="{wick_col}" stroke-width="1.6"/>'
            )
            elements.append(
                f'<rect x="{candle_x:.1f}" y="{body_top:.1f}" width="{CANDLE_W}" '
                f'height="{body_h:.1f}" fill="{color}" rx="1.5"/>'
            )
            if is_yesterday:
                elements.append(
                    f'<rect x="{candle_x - 2:.1f}" y="{body_top - 2:.1f}" '
                    f'width="{CANDLE_W + 4}" height="{body_h + 4:.1f}" fill="none" '
                    f'stroke="#fbbf24" stroke-width="1.5" rx="2" stroke-dasharray="3,2"/>'
                )
            if row.get('swing_high', False):
                elements.append(
                    f'<text x="{cx:.1f}" y="{y_high - 8:.1f}" text-anchor="middle" '
                    f'fill="#a78bfa" font-size="10">▲</text>'
                )
            if row.get('swing_low', False):
                elements.append(
                    f'<text x="{cx:.1f}" y="{y_low + 11:.1f}" text-anchor="middle" '
                    f'fill="#60a5fa" font-size="10">▼</text>'
                )
            try:
                date_label = row['date'].strftime('%m-%d')
            except Exception:
                date_label = str(row['date'])[:5]
            label_y = TOP_PAD + CHART_H + 14
            elements.append(
                f'<text x="{cx:.1f}" y="{label_y}" text-anchor="middle" '
                f'fill="#94a3b8" font-size="9" font-family="Consolas,monospace">{date_label}</text>'
            )
            if is_yesterday:
                elements.append(
                    f'<text x="{cx:.1f}" y="{label_y + 9}" text-anchor="middle" '
                    f'fill="#fbbf24" font-size="8" font-family="Consolas,monospace">전일</text>'
                )

        svg_body = "\n".join(elements)
        return f"""
<div class="candle-chart-wrap">
<div class="candle-chart-title">
📈 일봉 흐름
<span class="candle-chart-sub">최근 {n}일 · 전일 강조</span>
<span class="candle-chart-legend">
<span class="cc-leg-bull">■</span> 양봉
<span class="cc-leg-bear">■</span> 음봉
<span class="cc-leg-sw">▲▼</span> 스윙
</span>
</div>
<svg viewBox="0 0 {SVG_W} {SVG_H}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" style="display:block;border-radius:6px;overflow:hidden">
{svg_body}
</svg>
</div>"""
