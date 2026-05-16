# core/report_styles_v2.py
# 리포트 디자인 개선 오버라이드 CSS (v2)
# - 2열 그리드 (1920px 기준)  ← 4열에서 변경
# - 카드 상단 컬러 띠 (C2/C3/C4 + up/dn 배경 그라데이션)
# - 헤더 KPI 5개 (C2/C3/C4/SwH/SwL)
# - 카드 상단: summary (좌) + 일봉 미니차트 (우) 가로 배치
# - 1시간봉 캔들/파동: 카드 풀폭, 세로로 분리


def get_css_v2() -> str:
    return """
    /* ════════════════════════════════════════════════════════════
       🎨 Report Design v2 — Overrides
       ════════════════════════════════════════════════════════════ */

    /* ─── 헤더 KPI 영역 ─── */
    .header {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 32px;
      align-items: center;
    }
    .header-left { position: relative; }
    .header-kpi-row {
      display: flex;
      gap: 10px;
      align-items: center;
      position: relative;
    }
    .kpi {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-width: 86px;
      padding: 14px 16px;
      border-radius: var(--radius-md);
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.15);
      backdrop-filter: blur(4px);
    }
    .kpi-k {
      font-size: 0.74em;
      color: #cbd5e1;
      font-weight: 600;
      letter-spacing: 1px;
      text-transform: uppercase;
      margin-bottom: 4px;
    }
    .kpi-v {
      font-size: 1.8em;
      font-weight: 800;
      color: #f8fafc;
      line-height: 1;
      font-family: var(--font-mono);
    }
    .kpi-c2  { border-color: rgba(192,57,43,0.6);  background: linear-gradient(135deg, rgba(192,57,43,0.25),  rgba(192,57,43,0.08)); }
    .kpi-c2 .kpi-v  { color: #fecaca; }
    .kpi-c3  { border-color: rgba(211,84,0,0.6);   background: linear-gradient(135deg, rgba(211,84,0,0.25),   rgba(211,84,0,0.08)); }
    .kpi-c3 .kpi-v  { color: #fed7aa; }
    .kpi-c4  { border-color: rgba(30,132,73,0.6);  background: linear-gradient(135deg, rgba(30,132,73,0.25),  rgba(30,132,73,0.08)); }
    .kpi-c4 .kpi-v  { color: #bbf7d0; }
    .kpi-swh { border-color: rgba(124,58,237,0.6); background: linear-gradient(135deg, rgba(124,58,237,0.25), rgba(124,58,237,0.08)); }
    .kpi-swh .kpi-v { color: #ddd6fe; }
    .kpi-swl { border-color: rgba(29,78,216,0.6);  background: linear-gradient(135deg, rgba(29,78,216,0.25),  rgba(29,78,216,0.08)); }
    .kpi-swl .kpi-v { color: #bfdbfe; }

    /* ─── 카드 그리드: 2열 고정 (1920px 기준) ─── */
    .cards-grid {
      display: grid !important;
      grid-template-columns: repeat(2, 1fr) !important;
      gap: 24px !important;
    }
    .card {
      min-width: 0 !important;
      flex: none !important;
      padding: 0 !important;
      overflow: hidden;
      border-top: none !important;
      position: relative;
    }

    /* ─── 카드 상단 컬러 띠 ─── */
    .card-header-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 22px;
      color: #fff;
      font-weight: 700;
      letter-spacing: 0.3px;
    }
    .card-header-bar .chb-symbol { font-size: 1.15em; font-weight: 800; }
    .card-header-bar .chb-date {
      font-size: 0.78em;
      opacity: 0.9;
      background: rgba(255,255,255,0.18);
      padding: 4px 10px;
      border-radius: 999px;
      font-weight: 600;
    }
    .card-header-bar .chb-cnum {
      font-size: 0.82em;
      background: rgba(255,255,255,0.22);
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 700;
    }
    .card-header-bar .chb-dir { font-size: 1em; font-weight: 800; }

    .card-c2 .card-header-bar { background: linear-gradient(135deg, #c0392b, #e74c3c); }
    .card-c3 .card-header-bar { background: linear-gradient(135deg, #d35400, #e67e22); }
    .card-c4 .card-header-bar { background: linear-gradient(135deg, #1e8449, #27ae60); }
    .card-cn .card-header-bar { background: linear-gradient(135deg, #475569, #64748b); }

    .card.card-up {
      background:
        linear-gradient(180deg, rgba(16,185,129,0.06) 0%, transparent 110px),
        var(--bg-card);
    }
    .card.card-dn {
      background:
        linear-gradient(180deg, rgba(244,63,94,0.06) 0%, transparent 110px),
        var(--bg-card);
    }

    .card-body { padding: 20px 22px 22px; }
    .card > .card-title { display: none !important; }

    /* ─── 카드 상단 행: 좌(summary) + 우(일봉 미니차트) 가로 배치 ─── */
    .card-top-row {
      display: flex !important;
      flex-direction: row !important;
      align-items: stretch !important;
      gap: 16px !important;
      margin-bottom: 16px !important;
      flex-wrap: nowrap !important;
    }
    .summary-grid {
      flex: 1 1 0 !important;
      min-width: 0 !important;
      padding: 14px !important;
      gap: 10px !important;
    }
    .si { min-width: 72px !important; }
    .si-label { font-size: 0.66em !important; }
    .si-value { font-size: 0.88em !important; font-family: var(--font-mono); }

    /* 일봉 미니 캔들차트 — 카드 우측 고정 폭 */
    .candle-chart-wrap {
      width: 280px !important;
      flex: 0 0 280px !important;
      align-self: stretch;
    }
    .candle-chart-wrap svg {
      width: 100% !important;
      height: auto !important;
    }

    /* ─── 1시간봉: 캔들 / 파동 각각 카드 풀폭 ─── */
    .hourly-chart-stack {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 18px;
    }
    .hourly-chart-stack .hourly-chart-wrap {
      margin-bottom: 0 !important;
      padding: 12px 14px !important;
      width: 100%;
    }
    .hourly-svg-scroll {
      width: 100%;
      overflow-x: hidden;     /* 2열 카드에선 봉 24개가 풀폭에 여유롭게 들어감 */
    }
    .hourly-svg-scroll svg {
      display: block;
      width: 100% !important;
      height: auto !important;
    }

    /* ─── 기타 컴팩트 ─── */
    .weekly-ctx {
      gap: 10px !important;
      padding: 10px 14px !important;
      font-size: 0.82em !important;
    }
    .activity-box { padding: 12px 14px !important; font-size: 0.82em !important; }
    .activity-chart { height: 52px !important; }

    .interp { padding: 12px 16px !important; }
    .interp li { font-size: 0.82em !important; line-height: 1.9 !important; }

    .table-wrap { overflow-x: auto; }
    table { font-size: 0.82em !important; }
    th, td { padding: 7px 8px !important; }

    /* ─── 신호 요약 그리드 ─── */
    .signal-grid { gap: 16px !important; }

    /* ─── 반응형 ─── */
    @media (max-width: 1400px) {
      .cards-grid { grid-template-columns: 1fr !important; }
      .card-top-row { flex-wrap: wrap !important; }
      .candle-chart-wrap { width: 100% !important; flex: 1 1 auto !important; }
    }
    @media (max-width: 1100px) {
      .header { grid-template-columns: 1fr; }
      .header-kpi-row { flex-wrap: wrap; }
    }
    """
