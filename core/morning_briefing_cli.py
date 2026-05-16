# morning_briefing_cli.py
# 아침 브리핑 CLI 진입점 (Windows 작업 스케줄러용)
#
# 사용 예:
#   python morning_briefing_cli.py
#   python morning_briefing_cli.py --date 2026-05-09
#   python morning_briefing_cli.py --open
#
# Windows 작업 스케줄러 등록 예:
#   트리거: 매일 KST 08:00
#   동작:   python.exe
#   인수:   "C:\Users\gwakm\source\repos\Python_Code\Traiding_Daily_Briefing\morning_briefing_cli.py" --open
#   시작 위치: C:\Users\gwakm\source\repos\Python_Code\Traiding_Daily_Briefing

import argparse
import sys
import webbrowser
from datetime import date

from core.morning_worker import build_morning_briefing_sync


def main():
    parser = argparse.ArgumentParser(
        description="Daily Morning Briefing (RTH ORG + 일봉 신호)"
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="YYYY-MM-DD 형식 KST 기준일 (기본: 오늘)",
    )
    parser.add_argument(
        "--days", type=int, default=10,
        help="과거 갭 분석 기간 (기본: 10일)",
    )
    parser.add_argument(
        "--open", action="store_true",
        help="생성 후 브라우저에서 열기",
    )

    args = parser.parse_args()

    target = None
    if args.date:
        try:
            target = date.fromisoformat(args.date)
        except ValueError:
            print(f"❌ 날짜 형식 오류: {args.date} (YYYY-MM-DD)")
            sys.exit(1)

    try:
        path = build_morning_briefing_sync(
            target_date=target,
            days=args.days,
        )
    except Exception as e:
        print(f"❌ 브리핑 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"\n✅ 완료: {path}")

    if args.open:
        webbrowser.open(f"file:///{path}")


if __name__ == "__main__":
    main()
