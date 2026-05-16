# core/report_worker/worker.py
from __future__ import annotations
import traceback
from datetime import datetime, timezone, timedelta, date
from collections import defaultdict
from PyQt6.QtCore import QThread, pyqtSignal
from config import SESSION_CLOSE_HOUR
from core.report_builder import ReportBuilder
from ._utils import resample_to_hourly
from ._binance import collect_binance_data
from ._mt5 import collect_mt5_data

class ReportWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, object)
    error    = pyqtSignal(str)

    def __init__(
        self,
        selected: list[dict],
        manual_date=None,
        export_format: str = "HTML",
    ):
        super().__init__()
        self.selected      = selected
        self.manual_date   = manual_date
        self.export_format = export_format

    def _resolve_target_kst_date(self) -> date:
        if self.manual_date:
            return self.manual_date
        now_kst = datetime.now(timezone(timedelta(hours=9)))
        today   = now_kst.date()
        if now_kst.hour < SESSION_CLOSE_HOUR:
            target = today - timedelta(days=1)
        else:
            target = today
        # 주말 보정
        weekday = target.weekday()
        if weekday == 5:
            target -= timedelta(days=1)
        elif weekday == 6:
            target -= timedelta(days=2)
        return target

    def _emit_activity_diag(self, display_name: str, activity: dict | None):
        if activity is None:
            self.progress.emit(f"  [{display_name}] ⚠ 활발시간대 데이터 없음")
            return
        diag          = activity.get('_diag', {})
        matched       = diag.get('matched_candles', activity.get('total_candles', 0))
        covered       = diag.get('covered_hours', 0)
        target_date   = diag.get('target_date', '')
        tz_aware      = diag.get('tz_aware', False)
        self.progress.emit(
            f"  [{display_name}] 활발시간대 KST {target_date} | "
            f"매칭봉 {matched} | 커버시간 {covered}h | tz-aware={tz_aware}"
        )
        if covered < 12:
            self.progress.emit(f"  [{display_name}] ⚠ 커버 시간 부족 ({covered}h < 12h)")

    def run(self):
        try:
            now_utc = datetime.now(timezone.utc)
            now_kst = now_utc.astimezone(timezone(timedelta(hours=9)))
            self.progress.emit(
                f"리포트 생성 시작 | KST {now_kst.strftime('%Y-%m-%d %H:%M')} | UTC {now_utc.strftime('%Y-%m-%d %H:%M')}"
            )

            target_kst_date = self._resolve_target_kst_date()
            self.progress.emit(f"대상 KST 날짜: {target_kst_date}")

            # 🔧 브로커별 그룹핑 (KeyError 방지: defaultdict 사용)
            binance_items = []
            mt5_groups = defaultdict(list)  # ← 빈 dict({}) → defaultdict(list) 수정
            for item in self.selected:
                if 'binance' in item['broker'].lower():
                    binance_items.append(item)
                else:
                    mt5_groups[item['broker']].append(item)

            # Binance 수집
            b_data, b_weekly, b_act, b_hourly = collect_binance_data(
                binance_items, target_kst_date, self.progress.emit
            )
            # Binance 진단 로그
            for name in b_act:
                self._emit_activity_diag(name, b_act.get(name))
                n_h = len(b_hourly[name]) if b_hourly.get(name) else 0
                self.progress.emit(f"  [{name}] 1시간봉 {n_h}봉 생성 (KST {target_kst_date})")

            # MT5 수집
            m_data, m_weekly, m_act, m_hourly = collect_mt5_data(
                mt5_groups, target_kst_date, self.progress.emit
            )
            for name in m_act:
                self._emit_activity_diag(name, m_act.get(name))
                n_h = len(m_hourly[name]) if m_hourly.get(name) else 0
                self.progress.emit(f"  [{name}] 1시간봉 {n_h}봉 생성 (KST {target_kst_date})")

            # 데이터 병합
            all_data        = {**b_data, **m_data}
            all_weekly_data = {**b_weekly, **m_weekly}
            all_activity    = {**b_act, **m_act}
            all_hourly_data = {**b_hourly, **m_hourly}

            # 리포트 빌드
            self.progress.emit("리포트 HTML 빌드 중…")
            today_str     = now_kst.strftime('%Y-%m-%d')
            yesterday_str = str(target_kst_date)
            broker_label  = ', '.join(list(mt5_groups.keys()) + (['Binance'] if binance_items else [])) or '—'
            builder      = ReportBuilder()
            html_content = builder.build(
                all_data          = all_data,
                today_date        = today_str,
                yesterday_date    = yesterday_str,
                broker_name       = broker_label,
                all_weekly_data   = all_weekly_data,
                all_activity_data = all_activity,
                all_hourly_data   = all_hourly_data,
                manual_date       = self.manual_date,
            )

            # ★ 내보내기 형식 처리 (HTML / PNG / BOTH)
            html_path = builder.save(html_content, today_str)
            png_path  = None

            if self.export_format in ("PNG", "BOTH"):
                self.progress.emit("🖼 PNG 변환 중 (Playwright 렌더링, 고화질)…")
                png_path = builder.save_as_png(html_content, today_str)
                self.progress.emit(f"✅ PNG 저장 완료 → {png_path}")

            if self.export_format == "BOTH":
                self.progress.emit(f"✅ HTML 저장 완료 → {html_path}")
                self.finished.emit(html_path, target_kst_date)
            elif self.export_format == "PNG":
                self.finished.emit(png_path, target_kst_date)
            else:  # HTML
                self.progress.emit(f"✅ HTML 저장 완료 → {html_path}")
                self.finished.emit(html_path, target_kst_date)

        except Exception as e:
            self.error.emit(f"ReportWorker 치명적 오류: {e}\n{traceback.format_exc()}")