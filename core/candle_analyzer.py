# core/candle_analyzer.py
# 캔들 분석 로직 (꼬리/몸통 비율, 스윙 포인트, 캔들 번호, 해석 텍스트)

import pandas as pd
from config import CANDLE_THRESHOLDS, DECIMAL_PLACES


class CandleAnalyzer:

    def __init__(self):
        self.rw  = CANDLE_THRESHOLDS["reversal_wick"]
        self.rb  = CANDLE_THRESHOLDS["reversal_body"]
        self.eb  = CANDLE_THRESHOLDS["expansion_body"]
        self.ew  = CANDLE_THRESHOLDS["expansion_wick"]
        self.slb = CANDLE_THRESHOLDS["swing_lookback"]

    # --------------------------------
    # 전체 분석 파이프라인
    # --------------------------------
    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self._calc_basic(df)
        df = self._calc_swing(df)
        df = self._classify_candle(df)
        df = self._estimate_candle_num(df)
        return df

    # --------------------------------
    # 기본 수치 계산
    # --------------------------------
    def _calc_basic(self, df: pd.DataFrame) -> pd.DataFrame:
        df['range']      = df['high'] - df['low']
        df['body']       = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['direction']  = df.apply(
            lambda r: 'up' if r['close'] >= r['open'] else 'down', axis=1
        )
        df['eq'] = (df['high'] + df['low']) / 2

        def pct(val, rng):
            return round(val / rng * 100, 1) if rng > 0 else 0.0

        df['body_pct']       = df.apply(lambda r: pct(r['body'],       r['range']), axis=1)
        df['upper_wick_pct'] = df.apply(lambda r: pct(r['upper_wick'], r['range']), axis=1)
        df['lower_wick_pct'] = df.apply(lambda r: pct(r['lower_wick'], r['range']), axis=1)
        return df

    # --------------------------------
    # 스윙 고점 / 저점
    # --------------------------------
    def _calc_swing(self, df: pd.DataFrame) -> pd.DataFrame:
        n = self.slb
        df['swing_high'] = False
        df['swing_low']  = False
        for i in range(n, len(df) - n):
            if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, n+1)) and \
               all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, n+1)):
                df.at[i, 'swing_high'] = True
            if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, n+1)) and \
               all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, n+1)):
                df.at[i, 'swing_low'] = True
        return df

    # --------------------------------
    # 캔들 유형 분류
    # --------------------------------
    def _classify_candle(self, df: pd.DataFrame) -> pd.DataFrame:
        def classify(row):
            body     = row['body_pct']
            upper    = row['upper_wick_pct']
            lower    = row['lower_wick_pct']
            max_wick = max(upper, lower)

            if max_wick >= self.rw and body <= self.rb:
                return 'reversal_upper' if upper >= lower else 'reversal_lower'
            if body >= self.eb and upper <= self.ew and lower <= self.ew:
                return 'expansion'
            return 'neutral'

        df['candle_type'] = df.apply(classify, axis=1)
        return df

    # --------------------------------
    # 캔들 번호 추정 (C2 / C3 / C4)
    # --------------------------------
    def _estimate_candle_num(self, df: pd.DataFrame) -> pd.DataFrame:
        def estimate(i):
            if i < 2:
                return '-'
            cur   = df['candle_type'].iloc[i]
            prev1 = df['candle_type'].iloc[i-1]
            prev2 = df['candle_type'].iloc[i-2]

            if cur in ('reversal_upper', 'reversal_lower'):
                return 'C2'
            if prev1 in ('reversal_upper', 'reversal_lower') and cur == 'expansion':
                return 'C3'
            if prev2 in ('reversal_upper', 'reversal_lower') \
               and prev1 == 'expansion' and cur == 'expansion':
                return 'C4'
            return '-'

        df['candle_num'] = [estimate(i) for i in range(len(df))]
        return df

    # --------------------------------
    # 해석 텍스트 생성
    # --------------------------------
    def get_interpretation(self, df: pd.DataFrame, display_name: str, y_idx: int) -> list[str]:
        if df is None or len(df) < 5:
            return []

        yesterday = df.iloc[y_idx]
        prev1     = df.iloc[y_idx - 1]
        prev2     = df.iloc[y_idx - 2]
        lines     = []
        cnum      = yesterday['candle_num']
        direction = yesterday['direction']

        def f(val):
            dec = DECIMAL_PLACES.get(display_name, 5)
            return f"{val:,.{dec}f}" if dec > 0 else f"{val:,.0f}"

        if cnum == 'C2':
            if yesterday['upper_wick_pct'] >= yesterday['lower_wick_pct']:
                lines.append("위꼬리 반전 캔들 → 상방 레인지 소모")
                lines.append(f"꼬리 비율 {yesterday['upper_wick_pct']}% → 추가 하락 여력 제한적")
                lines.append("목표: Daily Open 또는 세션 저점 수준으로 낮게 설정")
                lines.append("→ 오늘(C3) 한 방향 연속 움직임 기대")
            else:
                lines.append("아래꼬리 반전 캔들 → 하방 레인지 소모")
                lines.append(f"꼬리 비율 {yesterday['lower_wick_pct']}% → 추가 상승 여력 제한적")
                lines.append("목표: Daily Open 또는 세션 고점 수준으로 낮게 설정")
                lines.append("→ 오늘(C3) 한 방향 연속 움직임 기대")
            lines.append(f"전일 EQ(0.5): {f(yesterday['eq'])}")

        elif cnum == 'C3':
            prev_max_wick = max(prev1['upper_wick_pct'], prev1['lower_wick_pct'])
            lines.append(f"전전일(C2) 꼬리 {prev_max_wick}% → C3 연속 흐름")
            if direction == 'up':
                lines.append("전일 상방 확장 마감")
                lines.append(f"전일 EQ(0.5): {f(yesterday['eq'])}")
                lines.append("→ 오늘(C4) 저점이 전일 EQ 위에서 형성되면 상방 강세 유효")
                lines.append("→ 전일 EQ 아래로 내려오면 강세 신호 약화")
            else:
                lines.append("전일 하방 확장 마감")
                lines.append(f"전일 EQ(0.5): {f(yesterday['eq'])}")
                lines.append("→ 오늘(C4) 고점이 전일 EQ 아래에서 형성되면 하방 약세 유효")
                lines.append("→ 전일 EQ 위로 올라오면 약세 신호 약화")

        elif cnum == 'C4':
            c3           = prev2
            c3_eq        = c3['eq']
            c3_high      = c3['high']
            c3_low       = c3['low']
            c3_upper_mid = (c3_high + c3_eq) / 2
            c3_lower_mid = (c3_eq + c3_low) / 2

            if direction == 'up':
                lines.append("C4 상방 연속")
                lines.append(f"C3 레인지: {f(c3_low)} ~ {f(c3_high)}")
                lines.append(f"C3 EQ: {f(c3_eq)} → 오늘 저점 기준선")
                lines.append(f"C3 상위절반 중간: {f(c3_upper_mid)}")
                lines.append("→ 오늘 저점이 C3 EQ 위에서 형성되어야 강세 유효")
                lines.append("→ C3 EQ 아래로 내려오면 강세 신호 약화")
            else:
                lines.append("C4 하방 연속")
                lines.append(f"C3 레인지: {f(c3_low)} ~ {f(c3_high)}")
                lines.append(f"C3 EQ: {f(c3_eq)} → 오늘 고점 기준선")
                lines.append(f"C3 하위절반 중간: {f(c3_lower_mid)}")
                lines.append("→ 오늘 고점이 C3 EQ 아래에서 형성되어야 약세 유효")
                lines.append("→ C3 EQ 위로 올라오면 약세 신호 약화")

        if yesterday['swing_high']:
            lines.append("⚠ 전일 스윙 고점 확인 → 반전 가능성 주시")
        if yesterday['swing_low']:
            lines.append("⚠ 전일 스윙 저점 확인 → 반전 가능성 주시")

        return lines
