# core/morning_worker.py
# 아침 브리핑 백그라운드 워커 + 동기 빌드 함수 (CLI/스케줄러용)

from datetime import datetime, date
from zoneinfo import ZoneInfo

from PyQt6.QtCore import QThread, pyqtSignal

from core.rth_org import run_rth_org_analysis
from core.morning_report_builder import MorningReportBuilder


KST = ZoneInfo("Asia/Seoul")


# ──────────────────────────────────────────────
# 동기 빌드 함수 (CLI / 스케줄러)
# ──────────────────────────────────────────────
def build_morning_briefing_sync(
    target_date: date | None = None,
    days: int = 10,
    progress_cb=None,
) -> str:
    """
    아침 브리핑 HTML 을 생성하고 저장 경로를 반환.

    target_date : KST 기준 날짜 (None 이면 오늘)
    days        : 과거 갭 분석 기간
    progress_cb : str -> None 콜백 (선택)
    """

    def emit(msg: str):
        if progress_cb:
            progress_cb(msg)
        else:
            print(msg)

    today_kst = target_date or datetime.now(tz=KST).date()
    emit(f"📅 분석 기준일 (KST): {today_kst}")

    # ── RTH ORG 통합 분석 ──
    emit("[1/2] RTH ORG 통합 분석 (US100, US500, KS200, HK50)...")
    rth_results = run_rth_org_analysis(
        symbols=["US100", "US500", "KS200", "HK50"],
        days=days,
        target_date=today_kst,
    )

    for sym, r in rth_results.items():
        if r is None:
            emit(f"   {sym} ✗ 데이터 없음")
        elif "error" in r:
            emit(f"   {sym} ✗ 오류: {r['error']}")
        else:
            gap = r.get("today_gap")
            if gap:
                emit(f"   {sym} ✓ 갭 {gap['gap_dir']} {gap['gap_abs']}pt")
            else:
                emit(f"   {sym} ✓ (갭 없음)")

    # ── HTML 빌드 ──
    emit("[2/2] HTML 리포트 생성...")
    builder = MorningReportBuilder()
    html    = builder.build(rth_results, today_kst)
    path    = builder.save(html, today_kst)

    emit(f"✅ 저장: {path}")
    return path


# ──────────────────────────────────────────────
# Qt 워커 스레드
# ──────────────────────────────────────────────
class MorningBriefingWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)   # 최종 HTML 경로
    error    = pyqtSignal(str)

    def __init__(self, target_date: date | None = None,
                 days: int = 10):
        super().__init__()
        self.target_date = target_date
        self.days        = days

    def run(self):
        try:
            now_kst = datetime.now(tz=KST)
            self.progress.emit(
                f"⏰ 현재 KST: {now_kst.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            path = build_morning_briefing_sync(
                target_date=self.target_date,
                days=self.days,
                progress_cb=self.progress.emit,
            )

            self.finished.emit(path)

        except Exception:
            import traceback
            self.error.emit(traceback.format_exc())
