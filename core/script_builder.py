# core/script_builder.py
# MQL5 스크립트 자동 생성 (조율자 역할)
# 레벨 수집 / MQL5 생성 로직은 각각 별도 모듈로 분리

import os
from datetime import datetime, date

from config import DECIMAL_PLACES, SCRIPTS_DIR, SYMBOLS
from core.mt5_connector import MT5Connector
from core.script_levels import ScriptLevelCollector
from core.script_mql5_generator import MQL5Generator


class ScriptBuilder:

    OBJ_PREFIX = "TB_"

    def __init__(self):
        self.level_collector = ScriptLevelCollector()
        self.mql5_generator  = MQL5Generator()

    # ── 브로커별 실제 MT5 심볼명 조회 ──
    def _get_broker_symbol(self, display_name: str, broker_name: str) -> str:
        for section in SYMBOLS.values():
            if display_name in section:
                return section[display_name].get(broker_name, display_name)
        return display_name

    # ── 메인 스크립트 생성 ──
    def build(
        self,
        display_name: str,
        df,
        broker_name: str,
        manual_date: date = None,
        weekly_df=None,
    ) -> str | None:
        if df is None or len(df) < 6:
            return None

        y_idx     = MT5Connector.get_yesterday_idx(df, manual_date)
        yesterday = df.iloc[y_idx]
        prev1     = df.iloc[y_idx - 1]
        prev2     = df.iloc[y_idx - 2]

        cnum      = yesterday['candle_num']
        direction = yesterday['direction']
        dec       = DECIMAL_PLACES.get(display_name, 5)

        # 레벨 수집
        levels = self.level_collector.collect(
            display_name=display_name,
            yesterday=yesterday,
            prev1=prev1,
            prev2=prev2,
            cnum=cnum,
            direction=direction,
            dec=dec,
            weekly_df=weekly_df,
            manual_date=manual_date,
        )

        expected_symbol = self._get_broker_symbol(display_name, broker_name)

        # MQL5 코드 생성
        mql5_code = self.mql5_generator.generate(
            display_name=display_name,
            levels=levels,
            broker_name=broker_name,
            dec=dec,
            cnum=cnum,
            expected_symbol=expected_symbol,
        )

        # 파일 저장
        if manual_date is not None:
            date_str = manual_date.strftime('%Y%m%d')
        else:
            date_str = datetime.today().strftime('%Y%m%d')

        filename = f"{display_name}_{date_str}.mq5"
        filepath = os.path.join(SCRIPTS_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(mql5_code)

        return filepath

    # ── 삭제 전용 스크립트 생성 ──
    def build_delete_script(self, display_name: str = None) -> str:
        code = self.mql5_generator.generate_delete_script(display_name)

        today_str = datetime.today().strftime('%Y-%m-%d')
        label     = display_name if display_name else "전체"
        filename  = f"Delete_{label}_{today_str}.mq5"
        filepath  = os.path.join(SCRIPTS_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        return filepath