def collect_mt5_data(
    broker_groups: dict[str, list[dict]],
    target_kst_date,
    progress_cb,
) -> tuple[dict, dict, dict, dict]:
    """
    MT5 브로커별 데이터 수집 → (all_data, all_weekly, all_activity, all_hourly) 반환
    """
    if not broker_groups:
        return {}, {}, {}, {}

    from core.mt5_connector     import MT5Connector
    from core.candle_analyzer   import CandleAnalyzer
    from core.intraday_analyzer import IntradayAnalyzer
    from ._utils import resample_to_hourly, INTRADAY_M5_COUNT

    all_data, all_weekly, all_activity, all_hourly = {}, {}, {}, {}

    for broker_name, items in broker_groups.items():
        progress_cb(f"[MT5:{broker_name}] 연결 중…")
        conn = MT5Connector(broker_name=broker_name)
        if not conn.connect():
            progress_cb(f"[MT5:{broker_name}] ❌ 연결 실패")
            continue

        analyzer = CandleAnalyzer()
        # 서버 timezone offset 추정
        server_offset = 2.0
        try:
            server_offset = conn.get_server_tz_offset_hours(display_name=items[0]['display_name'])
            progress_cb(f"[MT5:{broker_name}] 서버 오프셋 추정: GMT+{server_offset:.1f}")
            if not (0.0 <= server_offset <= 5.0):
                progress_cb(f"[MT5:{broker_name}] ⚠ 비정상 오프셋 ({server_offset}) → GMT+2 fallback")
                server_offset = 2.0
        except Exception:
            progress_cb(f"[MT5:{broker_name}] ⚠ 오프셋 추정 실패 → GMT+2 사용")

        for item in items:
            display_name = item['display_name']
            progress_cb(f"[MT5:{broker_name}] {display_name} 수집 중…")
            try:
                daily_df  = conn.get_daily_data(display_name, count=60)
                weekly_df = conn.get_weekly_data(display_name, count=20)
                m5_df     = conn.get_intraday_data(display_name, count=INTRADAY_M5_COUNT)

                if daily_df is None:
                    raise ValueError("일봉 데이터 없음")

                result = analyzer.analyze(daily_df)
                activity = None
                if m5_df is not None and not m5_df.empty:
                    intraday = IntradayAnalyzer()
                    activity = intraday.analyze(
                        df=m5_df, target_date=target_kst_date, source_tz_offset_hours=server_offset
                    )
                hourly = resample_to_hourly(m5_df, target_kst_date, server_offset=server_offset) if m5_df is not None else None

                all_data[display_name]        = result
                all_weekly[display_name]      = analyzer.analyze(weekly_df) if weekly_df is not None else None
                all_activity[display_name]    = activity
                all_hourly[display_name]      = hourly
            except Exception as e:
                progress_cb(f"  [{display_name}] ❌ 오류: {e}")
                all_data[display_name] = None
                all_weekly[display_name] = None
                all_activity[display_name] = None
                all_hourly[display_name] = None
        conn.disconnect()

    return all_data, all_weekly, all_activity, all_hourly