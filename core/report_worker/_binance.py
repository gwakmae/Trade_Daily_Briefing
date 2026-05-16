def collect_binance_data(
    selected_items: list[dict],
    target_kst_date,
    progress_cb,
) -> tuple[dict, dict, dict, dict]:
    """
    Binance 종목 데이터 수집 → (all_data, all_weekly, all_activity, all_hourly) 반환
    """
    if not selected_items:
        return {}, {}, {}, {}

    from core.binance_connector import BinanceConnector
    from core.candle_analyzer     import CandleAnalyzer
    from core.intraday_analyzer   import IntradayAnalyzer
    from ._utils import resample_to_hourly, INTRADAY_M5_COUNT

    bc       = BinanceConnector()
    analyzer = CandleAnalyzer()

    # ✅ 수정: 반환 변수명으로 통일 및 초기화
    all_data, all_weekly, all_activity, all_hourly = {}, {}, {}, {}

    for item in selected_items:
        display_name = item['display_name']
        progress_cb(f"[Binance] {display_name} 수집 중…")
        try:
            daily_df  = bc.get_daily_data(display_name, count=60)
            weekly_df = bc.get_weekly_data(display_name, count=20)
            m5_df     = bc.get_intraday_data(display_name, interval='5m', count=INTRADAY_M5_COUNT)

            if daily_df is None:
                raise ValueError("일봉 데이터 없음")

            result = analyzer.analyze(daily_df)
            activity = None
            if m5_df is not None and not m5_df.empty:
                intraday = IntradayAnalyzer()
                activity = intraday.analyze(
                    df=m5_df, target_date=target_kst_date, source_tz_offset_hours=0.0
                )
            hourly = resample_to_hourly(m5_df, target_kst_date, server_offset=0.0) if m5_df is not None else None

            # ✅ 수정: all_hourly 로 변수명 일치
            all_data[display_name]        = result
            all_weekly[display_name]      = analyzer.analyze(weekly_df) if weekly_df is not None else None
            all_activity[display_name]    = activity
            all_hourly[display_name]      = hourly
        except Exception as e:
            progress_cb(f"  [{display_name}] ❌ 오류: {e}")
            all_data[display_name]        = None
            all_weekly[display_name]      = None
            all_activity[display_name]    = None
            all_hourly[display_name]      = None

    return all_data, all_weekly, all_activity, all_hourly