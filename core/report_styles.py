# core/report_styles.py
from core.report_styles_v2 import get_css_v2


def get_css() -> str:
    """리포트 HTML에 임베드할 CSS 문자열 (v1 base + v2 overrides)"""
    return _get_css_v1() + "\n" + get_css_v2()


def _get_css_v1() -> str:
    """기존 v1 CSS (변경 없음)"""
    return """
    /* ════════════════════════════════════════════════════════════
       🎨 TTrades Daily Briefing — Modern Design System
       ════════════════════════════════════════════════════════════ */
    
    :root {
      --bg-page:      #f1f5f9;
      --bg-card:      #ffffff;
      --bg-card-alt:  #f8fafc;
      --border-light: #e2e8f0;
      --border-mid:   #cbd5e1;
      
      --text-primary:  #0f172a;
      --text-secondary:#475569;
      --text-muted:    #94a3b8;
      
      --accent-blue:   #3b82f6;
      --accent-indigo: #6366f1;
      --accent-emerald:#10b981;
      --accent-amber:  #f59e0b;
      --accent-rose:   #f43f5e;
      
      --up-color:      #059669;
      --up-bg:         #ecfdf5;
      --dn-color:      #dc2626;
      --dn-bg:         #fef2f2;
      
      --shadow-sm:     0 1px 2px rgba(0,0,0,0.05);
      --shadow-md:     0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1);
      --shadow-lg:     0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
      --shadow-xl:     0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);
      
      --radius-sm:     6px;
      --radius-md:     10px;
      --radius-lg:     16px;
      --radius-xl:     20px;
      
      --font-main:     'Inter', 'Segoe UI', 'Malgun Gothic', sans-serif;
      --font-mono:     'JetBrains Mono', 'Fira Code', Consolas, monospace;
    }

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: var(--font-main);
      background: var(--bg-page);
      color: var(--text-primary);
      padding: 32px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* ─── 헤더 ─── */
    .header {
      background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
      border-radius: var(--radius-xl);
      padding: 40px 48px 36px;
      margin-bottom: 36px;
      box-shadow: var(--shadow-lg);
      position: relative;
      overflow: hidden;
    }
    .header::before {
      content: '';
      position: absolute;
      top: -50%; right: -20%;
      width: 400px; height: 400px;
      background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
      pointer-events: none;
    }
    .header h1 {
      font-size: 1.8em;
      font-weight: 800;
      color: #f8fafc;
      letter-spacing: 0.5px;
      margin-bottom: 12px;
      position: relative;
    }
    .header .sub {
      color: #cbd5e1;
      font-size: 0.92em;
      line-height: 1.8;
      position: relative;
    }
    .header .sub span {
      color: #818cf8;
      font-weight: 600;
    }

    /* ─── 신호 요약 섹션 ─── */
    .signal-summary {
      background: linear-gradient(135deg, #fef3c7 0%, #fff7ed 100%);
      border: 1px solid #fcd34d;
      border-radius: var(--radius-lg);
      padding: 24px 28px;
      margin-bottom: 40px;
      box-shadow: var(--shadow-md);
    }
    .signal-title {
      font-size: 1.15em;
      font-weight: 700;
      color: #92400e;
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .signal-total {
      font-size: 0.75em;
      font-weight: 600;
      background: var(--accent-amber);
      color: #fff;
      padding: 3px 12px;
      border-radius: 999px;
    }
    .signal-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }
    .signal-col {
      background: var(--bg-card);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-light);
      overflow: hidden;
      box-shadow: var(--shadow-sm);
      transition: box-shadow 0.2s, transform 0.2s;
    }
    .signal-col:hover {
      box-shadow: var(--shadow-md);
      transform: translateY(-2px);
    }
    .signal-head {
      color: #fff;
      padding: 10px 14px;
      font-size: 0.88em;
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }
    .signal-head b { font-size: 1.1em; letter-spacing: 0.5px; }
    .signal-desc { opacity: 0.9; font-weight: 500; font-size: 0.85em; }
    .signal-cnt {
      margin-left: auto;
      background: rgba(255,255,255,0.25);
      padding: 2px 10px;
      border-radius: 999px;
      font-size: 0.8em;
      font-weight: 700;
    }
    .signal-list {
      list-style: none;
      padding: 8px 0;
      margin: 0;
    }
    .signal-list li {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-light);
      font-size: 0.85em;
      transition: background 0.15s;
    }
    .signal-list li:last-child { border-bottom: none; }
    .signal-list li:hover { background: var(--bg-card-alt); }
    .sig-link {
      text-decoration: none;
      color: var(--accent-indigo);
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }
    .sig-link:hover { color: #4f46e5; }
    .sig-dir { font-weight: 700; font-size: 0.9em; }
    .sig-dir.up { color: var(--up-color); }
    .sig-dir.dn { color: var(--dn-color); }
    .sig-detail {
      font-size: 0.78em;
      color: var(--text-secondary);
      margin-top: 4px;
      margin-left: 2px;
    }
    .signal-empty {
      padding: 24px 14px;
      color: var(--text-muted);
      font-size: 0.82em;
      text-align: center;
    }
    .signal-swing {
      margin-top: 16px;
      padding: 12px 18px;
      background: rgba(254,243,199,0.5);
      border-radius: var(--radius-sm);
      font-size: 0.84em;
      color: #78350f;
      border: 1px solid #fcd34d;
    }
    .signal-swing a {
      color: var(--accent-indigo);
      text-decoration: none;
      font-weight: 600;
    }
    .signal-swing a:hover { text-decoration: underline; }

    /* ─── 섹션 / 카드 ─── */
    .section { margin-bottom: 48px; }
    .section-title {
      font-size: 1.2em;
      color: var(--text-primary);
      border-left: 4px solid var(--accent-indigo);
      padding-left: 14px;
      margin-bottom: 20px;
      letter-spacing: 0.5px;
      font-weight: 700;
    }
    .cards-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
    }
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-light);
      border-radius: var(--radius-lg);
      padding: 24px;
      min-width: 400px;
      flex: 1;
      box-shadow: var(--shadow-md);
      scroll-margin-top: 20px;
      transition: box-shadow 0.25s, transform 0.25s;
    }
    .card:hover {
      box-shadow: var(--shadow-xl);
      transform: translateY(-3px);
    }
    .card-title {
      font-size: 1.1em;
      color: var(--accent-indigo);
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 10px;
      letter-spacing: 0.3px;
    }
    .card-date {
      font-size: 0.72em;
      color: var(--dn-color);
      font-weight: 600;
      background: var(--dn-bg);
      padding: 3px 10px;
      border-radius: 999px;
      border: 1px solid #fecaca;
    }
    .no-data { color: var(--dn-color); font-size: 0.85em; }

    /* ─── 카드 상단 행 ─── */
    .card-top-row {
      display: flex;
      align-items: flex-start;
      gap: 18px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }
    .summary-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      background: var(--bg-card-alt);
      border-radius: var(--radius-md);
      padding: 14px;
      border: 1px solid var(--border-light);
      flex: 1;
      min-width: 280px;
    }
    .si {
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 76px;
    }
    .si-label {
      font-size: 0.68em;
      color: var(--text-muted);
      margin-bottom: 4px;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .si-value {
      font-size: 0.9em;
      color: var(--text-primary);
      font-weight: 600;
    }

    /* ─── 4일봉 미니 캔들차트 ─── */
    .candle-chart-wrap {
      background: #1e293b;
      border-radius: var(--radius-md);
      padding: 12px 14px;
      border: 1px solid #334155;
      flex-shrink: 0;
      box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
    }
    .candle-chart-title {
      font-size: 0.78em;
      color: #94a3b8;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .candle-chart-sub { color: #64748b; font-size: 0.9em; }
    .candle-chart-legend {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.88em;
    }
    .cc-leg-bull { color: #22c55e; }
    .cc-leg-bear { color: #ef4444; }
    .cc-leg-sw   { color: #a78bfa; font-size: 0.85em; }

    /* ─── 전일 1시간봉 파동 차트 ─── */
    .hourly-chart-wrap {
      background: #0f172a;
      border: 1px solid #1e3a5f;
      border-radius: var(--radius-md);
      padding: 14px 16px;
      margin-bottom: 16px;
      box-shadow: inset 0 1px 4px rgba(0,0,0,0.4);
    }
    .hourly-chart-wrap.hourly-chart-empty {
      background: var(--bg-card-alt);
      border-color: var(--border-light);
    }
    .hourly-chart-title {
      font-size: 0.82em;
      color: #94a3b8;
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .hourly-chart-sub { color: #64748b; font-size: 0.9em; }
    .hourly-chart-legend {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85em;
      color: #94a3b8;
    }
    .hc-sess-as { color: #3b82f6; }
    .hc-sess-eu { color: #8b5cf6; }
    .hc-sess-ny { color: #f97316; }
    .hourly-empty-msg {
      color: var(--text-muted);
      font-size: 0.8em;
      padding: 10px 0;
      font-style: italic;
    }

    /* ─── 전주봉 컨텍스트 ─── */
    .weekly-ctx {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px;
      background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
      border: 1px solid #bfdbfe;
      border-radius: var(--radius-md);
      padding: 10px 16px;
      margin-bottom: 16px;
      font-size: 0.82em;
      color: var(--text-secondary);
    }
    .wk-label {
      font-weight: 700;
      color: var(--accent-indigo);
      margin-right: 6px;
      white-space: nowrap;
    }
    .wk-item { white-space: nowrap; color: var(--text-secondary); }
    .wk-item b { color: var(--text-primary); }

    /* ─── 활발 시간대 섹션 ─── */
    .activity-box {
      background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
      border: 1px solid #86efac;
      border-radius: var(--radius-md);
      padding: 14px 16px;
      margin-bottom: 16px;
      font-size: 0.82em;
      color: #14532d;
    }
    .activity-empty {
      background: var(--bg-card-alt);
      border-color: var(--border-light);
      color: var(--text-muted);
    }
    .activity-head {
      font-weight: 700;
      color: #166534;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .activity-empty .activity-head { color: var(--text-muted); }
    .activity-meta { font-weight: 500; color: var(--text-secondary); font-size: 0.88em; }
    .act-coverage-warn { color: #b45309; font-weight: 600; }
    .activity-top {
      margin-bottom: 10px;
      color: var(--text-secondary);
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .act-top-label {
      background: var(--accent-emerald);
      color: #fff;
      font-weight: 700;
      padding: 2px 10px;
      border-radius: 999px;
      font-size: 0.82em;
    }
    .act-top-item { color: #14532d; }
    .act-top-item b { color: #15803d; }
    .activity-chart {
      display: flex;
      align-items: flex-end;
      gap: 2px;
      height: 56px;
      padding: 6px 4px 0;
      background: rgba(255,255,255,0.7);
      border-radius: var(--radius-sm);
      border: 1px solid #d1fae5;
    }
    .act-bar-wrap {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
      justify-content: flex-end;
      cursor: help;
    }
    .act-bar {
      width: 100%;
      background: #86efac;
      border-radius: 2px 2px 0 0;
      min-height: 1px;
      transition: background 0.15s;
    }
    .act-bar-wrap:hover .act-bar { background: #4ade80; }
    .act-bar-top { background: #15803d !important; }
    .act-bar-empty { width: 100%; height: 1px; background: transparent; }
    .act-bar-label {
      font-size: 8px;
      color: var(--text-muted);
      margin-top: 2px;
      line-height: 1;
    }

    /* ─── 해석 텍스트 ─── */
    .interp {
      margin: 0 0 16px 0;
      padding: 14px 18px;
      background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
      border-left: 4px solid var(--accent-indigo);
      border-radius: var(--radius-sm);
      list-style: none;
      border: 1px solid #bfdbfe;
      border-left: 4px solid var(--accent-indigo);
    }
    .interp li {
      font-size: 0.82em;
      color: var(--text-secondary);
      line-height: 2;
      border-bottom: 1px solid #dbeafe;
    }
    .interp li:last-child { border-bottom: none; }

    /* ─── 테이블 ─── */
    .table-label {
      font-size: 0.78em;
      color: var(--text-muted);
      margin-bottom: 8px;
      letter-spacing: 0.5px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .table-wrap { overflow-x: auto; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8em;
      border-radius: var(--radius-md);
      overflow: hidden;
      border: 1px solid var(--border-light);
    }
    th {
      background: #f1f5f9;
      color: var(--text-secondary);
      padding: 10px 10px;
      text-align: center;
      border-bottom: 2px solid var(--border-mid);
      white-space: nowrap;
      font-weight: 700;
      font-size: 0.85em;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    td {
      padding: 8px 10px;
      text-align: center;
      border-bottom: 1px solid var(--border-light);
      white-space: nowrap;
      color: var(--text-primary);
    }
    tbody tr:nth-child(even) { background: var(--bg-card-alt); }
    tbody tr:hover td { background: #e0e7ff; }

    /* ─── 공통 ─── */
    .up { color: var(--up-color); font-weight: 700; }
    .dn { color: var(--dn-color); font-weight: 700; }
    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 0.78em;
      color: #fff;
      font-weight: 700;
    }
    .badge-swing-h { background: #7c3aed; }
    .badge-swing-l { background: #1d4ed8; }

    /* ─── 범례 ─── */
    .legend {
      margin-top: 48px;
      padding: 28px 32px;
      background: var(--bg-card);
      border-radius: var(--radius-lg);
      border: 1px solid var(--border-light);
      box-shadow: var(--shadow-sm);
    }
    .legend h3 {
      color: var(--text-primary);
      margin-bottom: 14px;
      font-size: 1em;
      letter-spacing: 0.5px;
      font-weight: 700;
    }
    .legend p { font-size: 0.82em; color: var(--text-secondary); line-height: 2; }

    /* ─── 반응형 ─── */
    @media (max-width: 900px) {
      .signal-grid  { grid-template-columns: 1fr; }
      .card-top-row { flex-direction: column; }
    }
    """
