from config import DECIMAL_PLACES

class SectionComponents:
    def weekly_context_html(self, wc: dict | None) -> str:
        if wc is None: return ""
        cnum_html = ""
        colors = {'C2': '#c0392b', 'C3': '#d35400', 'C4': '#1e8449'}
        if wc['candle_num'] in colors:
            cnum_html = f'<span class="badge" style="background:{colors[wc["candle_num"]]};font-size:0.72em">{wc["candle_num"]}</span>'
        swing_html = ""
        if wc['swing_high']: swing_html += '<span class="badge badge-swing-h" style="font-size:0.72em">SwH</span> '
        if wc['swing_low']: swing_html += '<span class="badge badge-swing-l" style="font-size:0.72em">SwL</span>'
        return f"""
<div class="weekly-ctx">
<span class="wk-label">전주봉 ({wc['week_date']} 마감)</span>
<span class="wk-item">고: <b>{wc['high']}</b></span>
<span class="wk-item">저: <b>{wc['low']}</b></span>
<span class="wk-item">EQ: <b>{wc['eq']}</b></span>
<span class="wk-item">몸통: <b>{wc['body_pct']}%</b></span>
<span class="wk-item" style="{self.fmt.wick_style(wc['upper_wick_pct'])}">위꼬리: <b>{wc['upper_wick_pct']}%</b></span>
<span class="wk-item" style="{self.fmt.wick_style(wc['lower_wick_pct'])}">아래꼬리: <b>{wc['lower_wick_pct']}%</b></span>
<span class="wk-item">유형: <b>{wc['candle_type']}</b></span>
{cnum_html}
{swing_html}
</div>"""

    def activity_section_html(self, activity: dict | None, display_name: str) -> str:
        if activity is None: return ""
        top, distribution, target_date, total = activity.get("top", []), activity.get("distribution", []), activity.get("target_date", ""), activity.get("total_candles", 0)
        if not distribution or total == 0:
            return f"""
<div class="activity-box activity-empty">
<div class="activity-head">🕐 활발 시간대 <span class="activity-meta">전일 {target_date} · 데이터 없음</span></div>
</div>"""
        dec = DECIMAL_PLACES.get(display_name, 5)
        def fmt_range(v): return f"{v:,.{dec}f}" if dec > 0 else f"{v:,.0f}"
        active_hours = sum(1 for d in distribution if d['avg_range'] > 0)
        coverage_note = f' <span class="act-coverage-warn">· {active_hours}/24시간만 거래</span>' if active_hours < 12 else ""
        top_html = ' · '.join(f'<span class="act-top-item"><b>{t["hour"]:02d}시</b> ({fmt_range(t["avg_range"])})</span>' for t in top) if top else '<span style="color:#9ca3af">데이터 부족</span>'
        bars_html = ""
        for d in distribution:
            hh, ratio, avg_r, cnt = d['hour'], d['ratio'], d['avg_range'], d['count']
            if avg_r == 0:
                bar_html_inner, tooltip = '<div class="act-bar act-bar-empty"></div>', f"{hh:02d}시 | 거래 없음"
            else:
                height_pct, is_top = max(4, int(ratio * 100)), any(t['hour'] == hh for t in top)
                bar_cls = "act-bar act-bar-top" if is_top else "act-bar"
                bar_html_inner = f'<div class="{bar_cls}" style="height:{height_pct}%"></div>'
                tooltip = f"{hh:02d}시 | 평균변동: {fmt_range(avg_r)} | 캔들수: {cnt}"
            bars_html += f'<div class="act-bar-wrap" title="{tooltip}">{bar_html_inner}<div class="act-bar-label">{hh:02d}</div></div>'
        return f"""
<div class="activity-box">
<div class="activity-head">🕐 활발 시간대 <span class="activity-meta">전일 {target_date} 5분봉 · KST · 총 {total}개{coverage_note}</span></div>
<div class="activity-top"><span class="act-top-label">TOP3</span> {top_html}</div>
<div class="activity-chart">{bars_html}</div>
</div>"""

    def signal_summary_html(self, buckets: dict, swing_highs: list, swing_lows: list) -> str:
        meta = {'C2': {'color': '#c0392b', 'desc': '반전 (1일차)'}, 'C3': {'color': '#d35400', 'desc': '확장 (2일차)'}, 'C4': {'color': '#1e8449', 'desc': '확장 (3일차)'}}
        cols_html = ""
        for cnum in ['C2', 'C3', 'C4']:
            items, color, desc = buckets[cnum], meta[cnum]['color'], meta[cnum]['desc']
            if not items: inner = '<p class="signal-empty">해당 신호 없음</p>'
            else:
                items_sorted = sorted(items, key=lambda x: 0 if x['direction_cls'] == 'up' else 1)
                rows = [f'<li><a href="#{it["anchor"]}" class="sig-link"><b>{it["symbol"]}</b><span class="sig-dir {it["direction_cls"]}">{it["direction"]}</span></a><div class="sig-detail">{it["detail"]}</div></li>' for it in items_sorted]
                inner = f'<ul class="signal-list">{"".join(rows)}</ul>'
            cols_html += f"""
<div class="signal-col">
<div class="signal-head" style="background:{color}"><b>{cnum}</b><span class="signal-desc">{desc}</span><span class="signal-cnt">{len(items)}</span></div>
{inner}
</div>"""
        swing_html = ""
        if swing_highs or swing_lows:
            sh_links = ', '.join(f'<a href="#{self.fmt.anchor_id(s)}">{s}</a>' for s in swing_highs) if swing_highs else '-'
            sl_links = ', '.join(f'<a href="#{self.fmt.anchor_id(s)}">{s}</a>' for s in swing_lows) if swing_lows else '-'
            swing_html = f"""
<div class="signal-swing">⚠ <b>스윙 포인트</b> &nbsp; <span class="badge badge-swing-h">SwH</span> {sh_links} &nbsp;|&nbsp; <span class="badge badge-swing-l">SwL</span> {sl_links}</div>"""
        total = sum(len(v) for v in buckets.values())
        return f"""
<div class="signal-summary">
<div class="signal-title">📌 오늘의 캔들 신호 요약 <span class="signal-total">총 {total}개 종목</span></div>
<div class="signal-grid">{cols_html}</div>
{swing_html}
</div>"""