# core/morning_report_builder.py
# 아침 브리핑 전용 HTML 리포트 빌더
#
# 구성:
#   1. 상단 요약 (오늘 KST + 시장 오픈 카운트다운)
#   2. 미국 마감 (US100, US500) — 확정된 RTH 갭/채움 결과
#   3. KS200 사전 분석 (오버나이트 흐름 + 일봉 신호 + 미채움 갭 레벨)
#   4. HK50 사전 분석 (동일 구성)
#   5. 일봉 캔들 신호 요약 (C2/C3/C4)
#   6. 활발 시간대

import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from config import REPORTS_DIR
from core.rth_org_config import RTH_ORG_SYMBOLS


KST = ZoneInfo("Asia/Seoul")


class MorningReportBuilder:

    # ──────────────────────────────────────────────
    # 시장 오픈 시각 (KST) 계산
    # ──────────────────────────────────────────────
    @staticmethod
    def _market_open_kst(symbol: str, today_kst: date) -> datetime | None:
        cfg = RTH_ORG_SYMBOLS.get(symbol)
        if cfg is None:
            return None

        # 서버(UTC+3) → KST(UTC+9) = +6시간
        # DST 보정은 미국만
        from core.rth_org_utils import is_us_dst

        open_h, open_m = cfg["rth_open"]
        if cfg.get("dst_aware") and not is_us_dst(today_kst):
            open_h += 1

        # 서버 시각 → KST
        kst_h = (open_h + 6) % 24
        day_offset = (open_h + 6) // 24

        target = datetime(
            today_kst.year, today_kst.month, today_kst.day,
            kst_h, open_m, tzinfo=KST,
        ) + timedelta(days=day_offset)

        return target

    # ──────────────────────────────────────────────
    # 카운트다운 텍스트
    # ──────────────────────────────────────────────
    @staticmethod
    def _countdown_text(target_dt: datetime, now_dt: datetime) -> str:
        if target_dt is None:
            return "-"

        diff = target_dt - now_dt
        total = int(diff.total_seconds())

        if total < 0:
            past = -total
            h = past // 3600
            m = (past % 3600) // 60
            return f"오픈 후 {h}h {m}m 경과"

        h = total // 3600
        m = (total % 3600) // 60
        return f"오픈까지 {h}h {m}m"

    # ──────────────────────────────────────────────
    # 갭 카드 (각 심볼별)
    # ──────────────────────────────────────────────
    def _build_gap_card(self, result: dict | None,
                       symbol: str, status_kind: str) -> str:
        """
        status_kind:
          - "confirmed" : 미국장처럼 이미 확정된 결과
          - "pending"   : KS200/HK50 처럼 오픈 전
        """
        cfg = RTH_ORG_SYMBOLS.get(symbol, {})
        dec = cfg.get("decimals", 2)

        if result is None or result.get("today_gap") is None:
            return f"""
            <div class="mr-card mr-card-empty">
                <div class="mr-card-head">
                    <span class="mr-sym">{symbol}</span>
                    <span class="mr-status mr-status-empty">데이터 없음</span>
                </div>
                <p class="mr-empty">RTH 갭 계산 불가 (데이터 부족 또는 휴장)</p>
            </div>"""

        if "error" in result:
            return f"""
            <div class="mr-card mr-card-empty">
                <div class="mr-card-head">
                    <span class="mr-sym">{symbol}</span>
                    <span class="mr-status mr-status-error">오류</span>
                </div>
                <p class="mr-empty">{result["error"]}</p>
            </div>"""

        gap   = result["today_gap"]
        fill  = result.get("today_fill")
        night = result.get("today_night_fill")

        gap_abs = gap["gap_abs"]
        gap_dir = gap["gap_dir"]

        dir_arrow = "▲" if gap_dir == "UP" else "▼"
        dir_cls   = "up" if gap_dir == "UP" else "dn"

        # 채움 상태
        if fill is None:
            fill_label = "갭 없음 / 미채움" if gap_abs < cfg.get("min_gap", 0) else "분석 불가"
            fill_cls   = "neutral"
        else:
            status = fill.get("fill_status", "")
            if status == "FILLED_100":
                fill_label, fill_cls = "✅ 100% 채움", "filled"
            elif status == "FILLED_50":
                fill_label, fill_cls = "🟡 50% 채움", "half"
            elif status_kind == "pending":
                fill_label, fill_cls = "⏳ 진행 전", "pending"
            else:
                fill_label, fill_cls = "🔴 미채움", "unfilled"

        night_html = ""
        if night is not None:
            n_label = []
            if night.get("night_fill_100"):
                n_label.append("100% 야간채움")
            elif night.get("night_fill_50"):
                n_label.append("50% 야간채움")
            else:
                n_label.append("야간 미채움")
            night_html = (
                f'<div class="mr-night">야간 세션: '
                f'<b>{" / ".join(n_label)}</b></div>'
            )

        f50_pct  = result.get("today_gap", {}).get("fill_50_pct", "")
        f100_pct = result.get("today_gap", {}).get("fill_100_pct", "")

        # classify_gap 결과
        size_label = gap.get("size_label", "-")

        # 미채움 레벨
        levels = result.get("unfilled_levels", {})
        res_levels = levels.get("resistance", [])[:3]
        sup_levels = levels.get("support", [])[:3]

        def fmt(v):
            return f"{v:,.{dec}f}" if dec > 0 else f"{v:,.0f}"

        levels_html = ""
        if res_levels or sup_levels:
            r_lines = "".join(
                f'<li><span class="mr-lv-date">{l["date"]}</span> '
                f'<span class="mr-lv-dir {l["gap_dir"].lower()}">{l["gap_dir"]}</span> '
                f'{fmt(l["gap_low"])} ~ {fmt(l["gap_high"])} '
                f'(50%: {fmt(l["gap_50"])})</li>'
                for l in res_levels
            ) or '<li class="mr-lv-empty">없음</li>'

            s_lines = "".join(
                f'<li><span class="mr-lv-date">{l["date"]}</span> '
                f'<span class="mr-lv-dir {l["gap_dir"].lower()}">{l["gap_dir"]}</span> '
                f'{fmt(l["gap_low"])} ~ {fmt(l["gap_high"])} '
                f'(50%: {fmt(l["gap_50"])})</li>'
                for l in sup_levels
            ) or '<li class="mr-lv-empty">없음</li>'

            levels_html = f"""
            <div class="mr-levels">
                <div class="mr-lv-block">
                    <div class="mr-lv-head mr-lv-resistance">▲ 저항 (위 미채움)</div>
                    <ul class="mr-lv-list">{r_lines}</ul>
                </div>
                <div class="mr-lv-block">
                    <div class="mr-lv-head mr-lv-support">▼ 지지 (아래 미채움)</div>
                    <ul class="mr-lv-list">{s_lines}</ul>
                </div>
            </div>"""

        # 핵심 가격 라인
        cp = result.get("current_price")
        cp_html = ""
        if cp is not None:
            cp_html = (
                f'<div class="mr-curp">현재가: <b>{fmt(cp)}</b></div>'
            )

        return f"""
        <div class="mr-card">
            <div class="mr-card-head">
                <span class="mr-sym">{symbol}</span>
                <span class="mr-dir {dir_cls}">{dir_arrow} {gap_dir}</span>
                <span class="mr-size">{size_label}</span>
                <span class="mr-status mr-status-{fill_cls}">{fill_label}</span>
            </div>
            <div class="mr-grid">
                <div><span class="mr-k">전일 RTH Close</span><span class="mr-v">{fmt(gap["rth_close"])}</span></div>
                <div><span class="mr-k">당일 RTH Open</span><span class="mr-v">{fmt(gap["rth_open"])}</span></div>
                <div><span class="mr-k">갭 크기</span><span class="mr-v">{fmt(gap_abs)}pt</span></div>
                <div><span class="mr-k">Gap High</span><span class="mr-v">{fmt(gap["gap_high"])}</span></div>
                <div><span class="mr-k">Gap 50%</span><span class="mr-v hl">{fmt(gap["gap_50"])}</span></div>
                <div><span class="mr-k">Gap Low</span><span class="mr-v">{fmt(gap["gap_low"])}</span></div>
            </div>
            {cp_html}
            {night_html}
            {levels_html}
        </div>"""

    # ──────────────────────────────────────────────
    # 섹션 빌드
    # ──────────────────────────────────────────────
    def _build_section(self, title: str, emoji: str,
                       results: dict, symbols: list[str],
                       status_kind: str, note: str = "") -> str:
        cards = "".join(
            self._build_gap_card(results.get(s), s, status_kind)
            for s in symbols
        )

        note_html = (
            f'<div class="mr-section-note">{note}</div>' if note else ""
        )

        return f"""
        <div class="mr-section">
            <div class="mr-section-title">
                {emoji} {title}
            </div>
            {note_html}
            <div class="mr-cards">{cards}</div>
        </div>"""

    # ──────────────────────────────────────────────
    # 메인 빌드
    # ──────────────────────────────────────────────
    def build(self, rth_results: dict,
              today_kst: date) -> str:

        now_kst = datetime.now(tz=KST)

        # 시장 오픈 카운트다운
        ks_open = self._market_open_kst("KS200", today_kst)
        hk_open = self._market_open_kst("HK50",  today_kst)

        ks_cd = self._countdown_text(ks_open, now_kst)
        hk_cd = self._countdown_text(hk_open, now_kst)

        # ── 섹션들 ──
        us_section = self._build_section(
            "미국 시장 마감 (확정)", "🇺🇸",
            rth_results, ["US100", "US500"],
            status_kind="confirmed",
            note="전일 미국 RTH 세션이 종료된 상태입니다. 갭 채움 결과가 확정되었습니다.",
        )

        ks_section = self._build_section(
            "KOSPI200 사전 점검", "🇰🇷",
            rth_results, ["KS200"],
            status_kind="pending",
            note=(
                f"KST 08:45 정규장 오픈 — <b>{ks_cd}</b>. "
                "오버나이트 갭(KST 06:00 야간세션 종료 → 정규장 오픈) 흐름 확인."
            ),
        )

        hk_section = self._build_section(
            "Hang Seng 사전 점검", "🇭🇰",
            rth_results, ["HK50"],
            status_kind="pending",
            note=(
                f"HKT 09:15 (KST 10:15) 정규장 오픈 — <b>{hk_cd}</b>. "
                "전일 HK 마감 이후 오버나이트 흐름 확인."
            ),
        )

        css = self._get_css()

        title_date = today_kst.strftime("%Y-%m-%d (%a)")
        gen_time   = now_kst.strftime("%Y-%m-%d %H:%M KST")

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>아침 브리핑 | {title_date}</title>
<style>{css}</style>
</head>
<body>

<div class="mr-header">
    <h1>🌅 Daily Morning Briefing</h1>
    <div class="mr-sub">
        <span>{title_date}</span>
        &nbsp;|&nbsp;
        생성: {gen_time}
    </div>
    <div class="mr-cd-row">
        <div class="mr-cd"><b>KS200</b> {ks_cd}</div>
        <div class="mr-cd"><b>HK50</b> {hk_cd}</div>
    </div>
</div>

{us_section}
{ks_section}
{hk_section}

<div class="mr-footer">
    <p>RTH ORG 분석은 5분봉 기준이며, 갭 50%/100% 채움 통계는 과거 백테스트 결과입니다.<br>
    KS200/HK50 은 오픈 전 시점이라 정규장 채움 결과가 아직 확정되지 않을 수 있습니다.<br>
    오픈 직후 새로고침하면 갭 채움 분석이 갱신됩니다.</p>
</div>

</body>
</html>"""

    # ──────────────────────────────────────────────
    # 저장
    # ──────────────────────────────────────────────
    def save(self, html: str, today_kst: date) -> str:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        morning_dir = os.path.join(REPORTS_DIR, "morning")
        os.makedirs(morning_dir, exist_ok=True)

        filename = f"morning_{today_kst.strftime('%Y%m%d')}.html"
        path = os.path.join(morning_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        return path

    # ──────────────────────────────────────────────
    # CSS
    # ──────────────────────────────────────────────
    @staticmethod
    def _get_css() -> str:
        return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
    background: #0f172a; color: #e2e8f0; padding: 24px;
}
.mr-header {
    text-align: center; padding: 20px;
    background: linear-gradient(135deg, #1e293b, #334155);
    border-radius: 12px; margin-bottom: 24px;
    border: 1px solid #475569;
}
.mr-header h1 {
    font-size: 1.7em; color: #fef3c7;
    letter-spacing: 2px; margin-bottom: 8px;
}
.mr-sub { color: #cbd5e1; font-size: 0.9em; }
.mr-sub span { color: #fbbf24; font-weight: 600; }
.mr-cd-row {
    display: flex; justify-content: center; gap: 16px;
    margin-top: 14px; flex-wrap: wrap;
}
.mr-cd {
    background: rgba(251, 191, 36, 0.15);
    color: #fde68a;
    padding: 6px 14px; border-radius: 20px;
    font-size: 0.85em; border: 1px solid #f59e0b;
}
.mr-cd b { color: #fef3c7; margin-right: 6px; }

.mr-section { margin-bottom: 32px; }
.mr-section-title {
    font-size: 1.15em; font-weight: 700; color: #f1f5f9;
    margin-bottom: 8px; padding-left: 12px;
    border-left: 4px solid #fbbf24;
    letter-spacing: 1px;
}
.mr-section-note {
    color: #94a3b8; font-size: 0.85em;
    margin-bottom: 12px; padding-left: 16px;
    line-height: 1.6;
}
.mr-section-note b { color: #fde68a; }

.mr-cards { display: flex; flex-wrap: wrap; gap: 14px; }

.mr-card {
    flex: 1 1 420px; min-width: 380px;
    background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.mr-card-empty {
    background: #1e293b; opacity: 0.7;
}
.mr-card-head {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 12px; flex-wrap: wrap;
    border-bottom: 1px solid #334155;
    padding-bottom: 10px;
}
.mr-sym {
    font-size: 1.15em; font-weight: 700;
    color: #fbbf24; letter-spacing: 1px;
}
.mr-dir { font-size: 1em; font-weight: 700; }
.mr-dir.up { color: #4ade80; }
.mr-dir.dn { color: #f87171; }
.mr-size {
    font-size: 0.82em; color: #cbd5e1;
    background: #0f172a; padding: 3px 8px;
    border-radius: 10px; border: 1px solid #334155;
}
.mr-status {
    margin-left: auto;
    font-size: 0.82em; font-weight: 600;
    padding: 4px 10px; border-radius: 6px;
}
.mr-status-filled   { background: #166534; color: #bbf7d0; }
.mr-status-half     { background: #854d0e; color: #fef3c7; }
.mr-status-unfilled { background: #991b1b; color: #fecaca; }
.mr-status-pending  { background: #1e40af; color: #dbeafe; }
.mr-status-neutral  { background: #475569; color: #e2e8f0; }
.mr-status-empty    { background: #475569; color: #cbd5e1; }
.mr-status-error    { background: #7f1d1d; color: #fecaca; }

.mr-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px 14px;
    margin-bottom: 10px;
}
.mr-grid > div {
    display: flex; flex-direction: column;
    background: #0f172a; padding: 6px 10px;
    border-radius: 6px; border: 1px solid #334155;
}
.mr-k { font-size: 0.7em; color: #94a3b8; }
.mr-v { font-size: 0.95em; color: #f1f5f9; font-weight: 600; }
.mr-v.hl { color: #fbbf24; }

.mr-curp {
    text-align: right;
    color: #cbd5e1;
    font-size: 0.85em;
    margin: 4px 0 8px;
}
.mr-curp b { color: #fbbf24; }

.mr-night {
    background: #1e3a8a; color: #dbeafe;
    padding: 6px 10px; border-radius: 6px;
    font-size: 0.82em; margin-top: 8px;
}

.mr-levels {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px; margin-top: 12px;
}
.mr-lv-block {
    background: #0f172a; border: 1px solid #334155;
    border-radius: 6px; padding: 8px 10px;
}
.mr-lv-head {
    font-size: 0.78em; font-weight: 600;
    margin-bottom: 4px; padding-bottom: 4px;
    border-bottom: 1px solid #334155;
}
.mr-lv-resistance { color: #f87171; }
.mr-lv-support    { color: #4ade80; }
.mr-lv-list { list-style: none; }
.mr-lv-list li {
    font-size: 0.78em; color: #cbd5e1;
    padding: 3px 0; line-height: 1.5;
}
.mr-lv-date {
    color: #94a3b8; margin-right: 4px;
    font-size: 0.9em;
}
.mr-lv-dir {
    display: inline-block; min-width: 38px;
    text-align: center; font-size: 0.75em;
    padding: 1px 5px; border-radius: 3px;
    margin-right: 4px;
}
.mr-lv-dir.up   { background: #14532d; color: #bbf7d0; }
.mr-lv-dir.down { background: #7f1d1d; color: #fecaca; }
.mr-lv-empty { color: #64748b; font-style: italic; }

.mr-empty {
    color: #94a3b8; font-style: italic;
    padding: 8px; font-size: 0.85em;
}

.mr-footer {
    margin-top: 32px; padding: 16px;
    background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; color: #94a3b8;
    font-size: 0.78em; line-height: 1.7;
}

@media (max-width: 700px) {
    .mr-grid    { grid-template-columns: 1fr 1fr; }
    .mr-levels  { grid-template-columns: 1fr; }
}
"""
