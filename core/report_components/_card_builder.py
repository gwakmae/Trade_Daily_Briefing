from core.mt5_connector import MT5Connector


class CardBuilder:
    def build_card(self, display_name: str, df, analyzer,
                   weekly_df=None, manual_date=None,
                   activity_data=None, hourly_data=None) -> str:
        anchor = self.fmt.anchor_id(display_name)

        # 데이터 없음 카드 (간단한 빈 카드)
        if df is None or len(df) < 6:
            return (
                f'<div class="card card-cn" id="{anchor}">'
                f'  <div class="card-header-bar">'
                f'    <span class="chb-symbol">{display_name}</span>'
                f'    <span class="chb-cnum">데이터 없음</span>'
                f'  </div>'
                f'  <div class="card-body"><p class="no-data">데이터 없음</p></div>'
                f'</div>'
            )

        y_idx       = MT5Connector.get_yesterday_idx(df, manual_date)
        yesterday   = df.iloc[y_idx]
        yd_str      = yesterday['date'].strftime('%Y-%m-%d')
        cnum        = yesterday['candle_num']
        direction   = yesterday['direction']
        dir_cls     = 'up' if direction == 'up' else 'dn'
        dir_arrow   = '↑' if direction == 'up' else '↓'
        dir_label   = '상승' if direction == 'up' else '하락'

        # 카드 모디파이어 클래스 (C2/C3/C4 + up/dn)
        cnum_cls = f"card-{cnum.lower()}" if cnum in ('C2', 'C3', 'C4') else "card-cn"
        card_cls = f"card {cnum_cls} card-{dir_cls}"

        # 카드 헤더 띠 — 캔들번호 배지는 cnum 있을 때만
        cnum_badge = f'<span class="chb-cnum">{cnum}</span>' if cnum in ('C2', 'C3', 'C4') else ''

        header_bar = f"""
<div class="card-header-bar">
  <span class="chb-symbol">{display_name}</span>
  <span class="chb-dir">{dir_arrow} {dir_label}</span>
  {cnum_badge}
  <span class="chb-date">전일 {yd_str}</span>
</div>"""

        prev3 = df.iloc[y_idx - 3:y_idx].copy()
        interp = analyzer.get_interpretation(df, display_name, y_idx)
        chart_html = self.candle_chart_html(df, y_idx, display_name, lookback=4)
        hourly_chart = self.hourly_chart_html(hourly_data, display_name)

        weekly_html = ""
        if weekly_df is not None and len(weekly_df) >= 3:
            try:
                weekly_analyzed = analyzer.analyze(weekly_df)
                w_idx = MT5Connector.get_last_week_idx(weekly_analyzed, reference_date=manual_date)
                wc = analyzer.get_weekly_context(weekly_analyzed, display_name, w_idx)
                weekly_html = self.weekly_context_html(wc)
            except Exception as e:
                weekly_html = f'<div class="weekly-ctx"><span class="wk-label">전주봉 로드 실패: {e}</span></div>'

        activity_html = self.activity_section_html(activity_data, display_name)

        interp_html = ""
        if interp:
            items = ''.join(f'<li>{line}</li>' for line in interp)
            interp_html = f'<ul class="interp">{items}</ul>'

        summary_items = [
            ("방향", self.fmt.direction_html(yesterday['direction'])),
            ("시가", self.fmt.fmt(yesterday['open'], display_name)),
            ("고가", self.fmt.fmt(yesterday['high'], display_name)),
            ("저가", self.fmt.fmt(yesterday['low'], display_name)),
            ("종가", self.fmt.fmt(yesterday['close'], display_name)),
            ("레인지", self.fmt.fmt(yesterday['range'], display_name)),
            ("EQ(0.5)", self.fmt.fmt(yesterday['eq'], display_name)),
            ("몸통%", f'<span style="{self.fmt.body_style(yesterday["body_pct"])}">{yesterday["body_pct"]}%</span>'),
            ("위꼬리%", f'<span style="{self.fmt.wick_style(yesterday["upper_wick_pct"])}">{yesterday["upper_wick_pct"]}%</span>'),
            ("아래꼬리%", f'<span style="{self.fmt.wick_style(yesterday["lower_wick_pct"])}">{yesterday["lower_wick_pct"]}%</span>'),
            ("스윙", self.fmt.swing_html(yesterday['swing_high'], yesterday['swing_low'])),
            ("유형", self.fmt.candle_type_label(yesterday['candle_type'])),
            ("캔들번호", self.fmt.candle_num_html(yesterday['candle_num'])),
        ]
        summary_html = ''.join(
            f'<div class="si"><span class="si-label">{k}</span><span class="si-value">{v}</span></div>'
            for k, v in summary_items
        )

        rows = ""
        for _, row in prev3.iterrows():
            rows += f"""<tr>
<td>{row['date'].strftime('%m-%d')}</td>
<td>{self.fmt.direction_html(row['direction'])}</td>
<td>{self.fmt.fmt(row['open'], display_name)}</td>
<td>{self.fmt.fmt(row['high'], display_name)}</td>
<td>{self.fmt.fmt(row['low'], display_name)}</td>
<td>{self.fmt.fmt(row['close'], display_name)}</td>
<td>{self.fmt.fmt(row['range'], display_name)}</td>
<td style="{self.fmt.body_style(row['body_pct'])}">{row['body_pct']}%</td>
<td style="{self.fmt.wick_style(row['upper_wick_pct'])}">{row['upper_wick_pct']}%</td>
<td style="{self.fmt.wick_style(row['lower_wick_pct'])}">{row['lower_wick_pct']}%</td>
<td>{self.fmt.fmt(row['eq'], display_name)}</td>
<td>{self.fmt.swing_html(row['swing_high'], row['swing_low'])}</td>
<td>{self.fmt.candle_type_label(row['candle_type'])}</td>
<td>{self.fmt.candle_num_html(row['candle_num'])}</td>
</tr>"""

        return f"""
<div class="{card_cls}" id="{anchor}">
{header_bar}
<div class="card-body">
<div class="card-top-row">
<div class="summary-grid">{summary_html}</div>
{chart_html}
</div>
{hourly_chart}
{weekly_html}
{activity_html}
{interp_html}
<div class="table-wrap">
<p class="table-label">이전 3일 흐름 (전일 제외)</p>
<table>
<thead><tr>
<th>날짜</th><th>방향</th><th>시가</th><th>고가</th><th>저가</th>
<th>종가</th><th>레인지</th><th>몸통%</th><th>위꼬리%</th>
<th>아래꼬리%</th><th>EQ</th><th>스윙</th><th>유형</th><th>캔들번호</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
</div>
</div>"""
