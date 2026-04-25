# core/report_builder.py
# HTML 리포트 생성

import os
from datetime import datetime
from config import SYMBOLS, DECIMAL_PLACES, CANDLE_THRESHOLDS, REPORTS_DIR
from core.mt5_connector import MT5Connector
from core.candle_analyzer import CandleAnalyzer


class ReportBuilder:

    def __init__(self):
        self.analyzer = CandleAnalyzer()
        self.rw  = CANDLE_THRESHOLDS["reversal_wick"]
        self.rb  = CANDLE_THRESHOLDS["reversal_body"]
        self.eb  = CANDLE_THRESHOLDS["expansion_body"]
        self.ew  = CANDLE_THRESHOLDS["expansion_wick"]
        self.slb = CANDLE_THRESHOLDS["swing_lookback"]

    def _fmt(self, val, display_name):
        dec = DECIMAL_PLACES.get(display_name, 5)
        return f"{val:,.0f}" if dec == 0 else f"{val:,.{dec}f}"

    def _direction_html(self, d):
        if d == 'up':
            return '<span class="up">↑ 상승</span>'
        return '<span class="dn">↓ 하락</span>'

    def _wick_style(self, pct):
        if pct >= self.rw:
            return 'color:#c0392b;font-weight:bold'
        elif pct >= 25:
            return 'color:#d35400;font-weight:bold'
        return ''

    def _body_style(self, pct):
        if pct >= self.eb:
            return 'color:#1e8449;font-weight:bold'
        return ''

    def _swing_html(self, sh, sl):
        r = []
        if sh:
            r.append('<span class="badge badge-swing-h">SwH</span>')
        if sl:
            r.append('<span class="badge badge-swing-l">SwL</span>')
        return ' '.join(r) if r else '-'

    def _candle_num_html(self, cn):
        colors = {'C2': '#c0392b', 'C3': '#d35400', 'C4': '#1e8449'}
        if cn in colors:
            return f'<span class="badge" style="background:{colors[cn]}">{cn}</span>'
        return '<span style="color:#aaa">-</span>'

    def _candle_type_label(self, ct):
        return {
            'reversal_upper': '반전(위꼬리)',
            'reversal_lower': '반전(아래꼬리)',
            'expansion':      '확장',
            'neutral':        '-'
        }.get(ct, '-')

    def _build_card(self, display_name, df):
        if df is None or len(df) < 6:
            return f'<div class="card"><div class="card-title">{display_name}</div><p class="no-data">데이터 없음</p></div>'

        y_idx     = MT5Connector.get_yesterday_idx(df)
        yesterday = df.iloc[y_idx]
        yd_str    = yesterday['date'].strftime('%Y-%m-%d')
        prev3     = df.iloc[y_idx-3:y_idx].copy()
        interp    = self.analyzer.get_interpretation(df, display_name, y_idx)

        interp_html = ""
        if interp:
            items = ''.join(f'<li>{line}</li>' for line in interp)
            interp_html = f'<ul class="interp">{items}</ul>'

        summary_items = [
            ("방향",      self._direction_html(yesterday['direction'])),
            ("시가",      self._fmt(yesterday['open'],  display_name)),
            ("고가",      self._fmt(yesterday['high'],  display_name)),
            ("저가",      self._fmt(yesterday['low'],   display_name)),
            ("종가",      self._fmt(yesterday['close'], display_name)),
            ("레인지",    self._fmt(yesterday['range'], display_name)),
            ("EQ(0.5)",   self._fmt(yesterday['eq'],    display_name)),
            ("몸통%",     f'<span style="{self._body_style(yesterday["body_pct"])}">{yesterday["body_pct"]}%</span>'),
            ("위꼬리%",   f'<span style="{self._wick_style(yesterday["upper_wick_pct"])}">{yesterday["upper_wick_pct"]}%</span>'),
            ("아래꼬리%", f'<span style="{self._wick_style(yesterday["lower_wick_pct"])}">{yesterday["lower_wick_pct"]}%</span>'),
            ("스윙",      self._swing_html(yesterday['swing_high'], yesterday['swing_low'])),
            ("유형",      self._candle_type_label(yesterday['candle_type'])),
            ("캔들번호",  self._candle_num_html(yesterday['candle_num'])),
        ]
        summary_html = ''.join(
            f'<div class="si"><span class="si-label">{k}</span><span class="si-value">{v}</span></div>'
            for k, v in summary_items
        )

        rows = ""
        for _, row in prev3.iterrows():
            rows += f"""<tr>
                <td>{row['date'].strftime('%m-%d')}</td>
                <td>{self._direction_html(row['direction'])}</td>
                <td>{self._fmt(row['open'],  display_name)}</td>
                <td>{self._fmt(row['high'],  display_name)}</td>
                <td>{self._fmt(row['low'],   display_name)}</td>
                <td>{self._fmt(row['close'], display_name)}</td>
                <td>{self._fmt(row['range'], display_name)}</td>
                <td style="{self._body_style(row['body_pct'])}">{row['body_pct']}%</td>
                <td style="{self._wick_style(row['upper_wick_pct'])}">{row['upper_wick_pct']}%</td>
                <td style="{self._wick_style(row['lower_wick_pct'])}">{row['lower_wick_pct']}%</td>
                <td>{self._fmt(row['eq'], display_name)}</td>
                <td>{self._swing_html(row['swing_high'], row['swing_low'])}</td>
                <td>{self._candle_type_label(row['candle_type'])}</td>
                <td>{self._candle_num_html(row['candle_num'])}</td>
            </tr>"""

        return f"""
        <div class="card">
            <div class="card-title">
                {display_name}
                <span class="card-date">전일 {yd_str} 마감 기준</span>
            </div>
            <div class="summary-grid">{summary_html}</div>
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
        </div>"""

    def build(self, all_data: dict, today_date: str, yesterday_date: str,
              broker_name: str) -> str:

        sections_html = ""
        for section, symbols_dict in SYMBOLS.items():
            cards = ""
            for display_name in symbols_dict:
                if display_name in all_data:
                    cards += self._build_card(display_name, all_data[display_name])
            if cards:
                sections_html += f"""
                <div class="section">
                    <div class="section-title">{section}</div>
                    <div class="cards-grid">{cards}</div>
                </div>"""

        css = self._get_css()
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>일봉 브리핑 | {today_date}</title>
<style>{css}</style>
</head>
<body>
<div class="header">
    <h1>📊 일봉 브리핑 리포트</h1>
    <div class="sub">
        보고서 생성일: <span>{today_date}</span>
        &nbsp;|&nbsp;
        분석 기준: 전일 <span>{yesterday_date}</span> 마감 캔들
        &nbsp;|&nbsp;
        {broker_name}
    </div>
</div>
{sections_html}
{self._get_legend()}
</body>
</html>"""

    def save(self, html_content: str, today_date: str) -> str:
        filename    = f"daily_report_{today_date}.html"
        output_path = os.path.join(REPORTS_DIR, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path

    def _get_css(self):
        return """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI','Malgun Gothic',sans-serif;background:#e8eaed;color:#2c2c2c;padding:24px}
.header{text-align:center;padding:24px 0 32px;border-bottom:2px solid #c8ccd2;margin-bottom:28px;background:#f5f6f8;border-radius:10px}
.header h1{font-size:1.7em;color:#1a1a2e;letter-spacing:3px}
.header .sub{color:#666;margin-top:8px;font-size:0.88em;line-height:1.8}
.header .sub span{color:#2563eb;font-weight:600}
.section{margin-bottom:44px}
.section-title{font-size:1.05em;color:#444;border-left:4px solid #2563eb;padding-left:12px;margin-bottom:16px;letter-spacing:1px;font-weight:600}
.cards-grid{display:flex;flex-wrap:wrap;gap:16px}
.card{background:#f5f6f8;border:1px solid #d1d5db;border-radius:10px;padding:18px;min-width:380px;flex:1;box-shadow:0 1px 4px rgba(0,0,0,0.07)}
.card-title{font-size:1.05em;color:#1d4ed8;font-weight:bold;margin-bottom:6px;letter-spacing:1px;display:flex;align-items:center;gap:10px}
.card-date{font-size:0.75em;color:#dc2626;font-weight:normal;background:#fef2f2;padding:2px 8px;border-radius:4px;border:1px solid #fca5a5}
.no-data{color:#dc2626;font-size:0.85em}
.summary-grid{display:flex;flex-wrap:wrap;gap:8px;background:#eef0f3;border-radius:8px;padding:12px;margin-bottom:12px;margin-top:10px;border:1px solid #d1d5db}
.si{display:flex;flex-direction:column;align-items:center;min-width:72px}
.si-label{font-size:0.68em;color:#888;margin-bottom:3px}
.si-value{font-size:0.88em;color:#1a1a2e;font-weight:500}
.interp{margin:0 0 12px 0;padding:10px 14px;background:#eff6ff;border-left:3px solid #2563eb;border-radius:4px;list-style:none;border:1px solid #bfdbfe}
.interp li{font-size:0.8em;color:#374151;line-height:1.9;border-bottom:1px solid #dbeafe}
.interp li:last-child{border-bottom:none}
.table-label{font-size:0.75em;color:#888;margin-bottom:6px;letter-spacing:1px}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:0.78em}
th{background:#e2e5ea;color:#555;padding:6px 8px;text-align:center;border-bottom:2px solid #c8ccd2;white-space:nowrap;font-weight:600}
td{padding:5px 8px;text-align:center;border-bottom:1px solid #e5e7eb;white-space:nowrap;color:#374151}
tr:hover td{background:#eef0f3}
.up{color:#15803d;font-weight:bold}
.dn{color:#dc2626;font-weight:bold}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:0.8em;color:#fff;font-weight:bold}
.badge-swing-h{background:#7c3aed}
.badge-swing-l{background:#1d4ed8}
.legend{margin-top:40px;padding:20px;background:#f5f6f8;border-radius:10px;border:1px solid #d1d5db}
.legend h3{color:#555;margin-bottom:10px;font-size:0.9em;letter-spacing:1px;font-weight:600}
.legend p{font-size:0.78em;color:#666;line-height:2}
"""

    def _get_legend(self):
        return f"""
<div class="legend">
    <h3>📌 범례 및 분류 기준</h3>
    <p>
    <b>반전 캔들:</b> 최대꼬리 ≥ {self.rw}% AND 몸통 ≤ {self.rb}%<br>
    <b>확장 캔들:</b> 몸통 ≥ {self.eb}% AND 위/아래꼬리 각각 ≤ {self.ew}%<br>
    <b>C2:</b> 전일 반전캔들 &nbsp;|&nbsp;
    <b>C3:</b> 전전일 반전 + 전일 확장 &nbsp;|&nbsp;
    <b>C4:</b> 3일전 반전 + 전전일 확장 + 전일 확장<br>
    <b>SwH:</b> 양쪽 {self.slb}캔들보다 고가 높음 &nbsp;|&nbsp;
    <b>SwL:</b> 양쪽 {self.slb}캔들보다 저가 낮음<br>
    <b>색상:</b> 🟢 확장몸통(≥{self.eb}%) &nbsp;|&nbsp;
    🔴 큰꼬리(≥{self.rw}%) &nbsp;|&nbsp;
    🟠 중간꼬리(25~{self.rw}%)
    </p>
</div>"""
