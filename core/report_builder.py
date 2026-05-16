# core/report_builder.py
# HTML 리포트 생성 (조율자 역할)
import os
from datetime import datetime
from config import SYMBOLS, CANDLE_THRESHOLDS, REPORTS_DIR
from core.mt5_connector import MT5Connector
from core.candle_analyzer import CandleAnalyzer
from core.report_formatter import ReportFormatter
from core.report_components import ReportComponents
from core.report_styles import get_css


class ReportBuilder:
    def __init__(self):
        self.analyzer   = CandleAnalyzer()
        self.fmt        = ReportFormatter()
        self.components = ReportComponents(self.fmt)

    def _extract_signal_info(self, display_name, df, y_idx) -> dict:
        y     = df.iloc[y_idx]
        cnum  = y['candle_num']
        direction_arrow = '↑' if y['direction'] == 'up' else '↓'
        direction_cls   = 'up' if y['direction'] == 'up' else 'dn'
        info = {
            'symbol':        display_name,
            'cnum':          cnum,
            'direction':     direction_arrow,
            'direction_cls': direction_cls,
            'eq':            self.fmt.fmt(y['eq'], display_name),
            'anchor':        self.fmt.anchor_id(display_name),
            'detail':        '',
        }
        if cnum == 'C2':
            if y['upper_wick_pct'] >= y['lower_wick_pct']:
                info['detail'] = f"위꼬리 {y['upper_wick_pct']}% · EQ {info['eq']}"
            else:
                info['detail'] = f"아래꼬리 {y['lower_wick_pct']}% · EQ {info['eq']}"
        elif cnum == 'C3':
            info['detail'] = f"EQ {info['eq']} (오늘 기준선)"
        elif cnum == 'C4':
            try:
                c3      = df.iloc[y_idx - 2]
                c3_eq   = self.fmt.fmt(c3['eq'],   display_name)
                c3_high = self.fmt.fmt(c3['high'], display_name)
                c3_low  = self.fmt.fmt(c3['low'],  display_name)
                info['detail'] = f"C3 EQ {c3_eq} · 레인지 {c3_low}~{c3_high}"
            except Exception:
                info['detail'] = f"EQ {info['eq']}"
        return info

    def _collect_signal_buckets(self, all_data: dict, manual_date=None) -> tuple:
        """C2/C3/C4 버킷 + 스윙 리스트 집계 (KPI 헤더 + 요약 공용)"""
        buckets = {'C2': [], 'C3': [], 'C4': []}
        swing_highs = []
        swing_lows  = []
        for display_name, df in all_data.items():
            if df is None or len(df) < 6:
                continue
            try:
                y_idx = MT5Connector.get_yesterday_idx(df, manual_date)
                y     = df.iloc[y_idx]
                cnum  = y['candle_num']
                if cnum in buckets:
                    info = self._extract_signal_info(display_name, df, y_idx)
                    buckets[cnum].append(info)
                if y['swing_high']:
                    swing_highs.append(display_name)
                if y['swing_low']:
                    swing_lows.append(display_name)
            except Exception:
                continue
        return buckets, swing_highs, swing_lows

    def _build_signal_summary(self, buckets, swing_highs, swing_lows) -> str:
        if not any(buckets.values()) and not swing_highs and not swing_lows:
            return ""
        return self.components.signal_summary_html(buckets, swing_highs, swing_lows)

    def _build_header_kpi(self, buckets, swing_highs, swing_lows) -> str:
        """헤더 우측 KPI 5개 (C2/C3/C4/SwH/SwL)"""
        c2 = len(buckets.get('C2', []))
        c3 = len(buckets.get('C3', []))
        c4 = len(buckets.get('C4', []))
        sh = len(swing_highs)
        sl = len(swing_lows)
        return f"""
<div class="header-kpi-row">
  <div class="kpi kpi-c2"><span class="kpi-k">C2</span><span class="kpi-v">{c2}</span></div>
  <div class="kpi kpi-c3"><span class="kpi-k">C3</span><span class="kpi-v">{c3}</span></div>
  <div class="kpi kpi-c4"><span class="kpi-k">C4</span><span class="kpi-v">{c4}</span></div>
  <div class="kpi kpi-swh"><span class="kpi-k">SwH</span><span class="kpi-v">{sh}</span></div>
  <div class="kpi kpi-swl"><span class="kpi-k">SwL</span><span class="kpi-v">{sl}</span></div>
</div>"""

    def build(self, all_data: dict, today_date: str,
              yesterday_date: str, broker_name: str,
              all_weekly_data: dict = None,
              all_activity_data: dict = None,
              all_hourly_data: dict = None,
              manual_date=None) -> str:

        # 신호 집계 (KPI + 요약 공용)
        buckets, swing_highs, swing_lows = self._collect_signal_buckets(
            all_data, manual_date
        )
        summary_html = self._build_signal_summary(buckets, swing_highs, swing_lows)
        kpi_html     = self._build_header_kpi(buckets, swing_highs, swing_lows)

        # 카드 빌드 — manual_date 만 카드에 전달, 카드 빌더가 내부에서
        # y_idx 기반으로 cnum/direction 추출하여 모디파이어 클래스 부여함
        sections_html = ""
        for section, symbols_dict in SYMBOLS.items():
            cards = ""
            for display_name in symbols_dict:
                if display_name in all_data:
                    weekly_df     = None
                    activity_data = None
                    hourly_data   = None
                    if all_weekly_data:
                        weekly_df = all_weekly_data.get(display_name)
                    if all_activity_data:
                        activity_data = all_activity_data.get(display_name)
                    if all_hourly_data:
                        hourly_data = all_hourly_data.get(display_name)
                    cards += self.components.build_card(
                        display_name=display_name,
                        df=all_data[display_name],
                        analyzer=self.analyzer,
                        weekly_df=weekly_df,
                        manual_date=manual_date,
                        activity_data=activity_data,
                        hourly_data=hourly_data,
                    )
            if cards:
                sections_html += f"""
<div class="section">
  <div class="section-title">{section}</div>
  <div class="cards-grid">{cards}</div>
</div>"""

        manual_note = (
            f' <span style="color:#dc2626;font-size:0.85em">'
            f'[수동 지정: {manual_date}]</span>'
            if manual_date else ""
        )
        css = get_css()
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
    <div class="header-left">
      <h1>📊 일봉 브리핑 리포트</h1>
      <div class="sub">
        보고서 생성일: <span>{today_date}</span>
        &nbsp;|&nbsp;
        분석 기준: 전일 <span>{yesterday_date}</span> 마감 캔들
        {manual_note}
        &nbsp;|&nbsp;
        {broker_name}
      </div>
    </div>
    {kpi_html}
  </div>
  {summary_html}
  {sections_html}
  {self.components.legend_html()}
</body>
</html>"""

    def save(self, html_content: str, today_date: str) -> str:
        filename    = f"daily_report_{today_date}.html"
        output_path = os.path.join(REPORTS_DIR, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path

    def save_as_png(self, html_content: str, today_date: str,
                    output_dir: str = None) -> str:
        from core.report_png_exporter import html_to_png
        if output_dir is None:
            output_dir = REPORTS_DIR
        os.makedirs(output_dir, exist_ok=True)
        filename = f"daily_report_{today_date}.png"
        output_path = os.path.join(output_dir, filename)
        html_to_png(
            html_content=html_content,
            output_path=output_path,
            width=1920,
            height=1080,
            scale=2.0
        )
        return output_path
