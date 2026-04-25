# core/script_builder.py
# MQL5 스크립트 자동 생성

import os
from datetime import datetime
from config import DECIMAL_PLACES, SCRIPTS_DIR
from core.mt5_connector import MT5Connector


class ScriptBuilder:

    OBJ_PREFIX = "TB_"

    # --------------------------------
    # 메인 스크립트 생성
    # --------------------------------
    def build(self, display_name: str, df, broker_name: str) -> str | None:
        if df is None or len(df) < 6:
            return None

        y_idx     = MT5Connector.get_yesterday_idx(df)
        yesterday = df.iloc[y_idx]
        prev1     = df.iloc[y_idx - 1]
        prev2     = df.iloc[y_idx - 2]

        cnum      = yesterday['candle_num']
        direction = yesterday['direction']
        dec       = DECIMAL_PLACES.get(display_name, 5)

        levels = self._collect_levels(
            display_name, yesterday, prev1, prev2, cnum, direction, dec
        )

        mql5_code = self._generate_mql5(
            display_name, levels, broker_name, dec, yesterday, cnum
        )

        today_str = datetime.today().strftime('%Y%m%d')
        filename  = f"{display_name}_{today_str}.mq5"
        filepath  = os.path.join(SCRIPTS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(mql5_code)

        return filepath

    # --------------------------------
    # 레벨 수집
    # --------------------------------
    def _collect_levels(self, display_name, yesterday, prev1, prev2,
                        cnum, direction, dec):
        levels = []

        def f(v):
            return f"{v:.{dec}f}"

        def add(name, value, color, style=0, width=1, label=""):
            levels.append({
                "name":  name,
                "value": value,
                "color": color,
                "style": style,
                "width": width,
                "label": label if label else name,
            })

        # 전일 공통 레벨
        add("PrevHigh",  yesterday['high'],  "clrRed",
            style=0, width=1,
            label=f"PrevHigh : {f(yesterday['high'])}")

        add("PrevLow",   yesterday['low'],   "clrRoyalBlue",
            style=0, width=1,
            label=f"PrevLow : {f(yesterday['low'])}")

        add("PrevOpen",  yesterday['open'],  "clrGray",
            style=2, width=1,
            label=f"PrevOpen : {f(yesterday['open'])}")

        add("PrevClose", yesterday['close'], "clrDimGray",
            style=2, width=1,
            label=f"PrevClose : {f(yesterday['close'])}")

        add("PrevEQ",    yesterday['eq'],    "clrDarkOrange",
            style=1, width=2,
            label=f"PrevEQ(0.5) : {f(yesterday['eq'])}")

        # C3 핵심 기준선
        if cnum == 'C3':
            add("C3_EQ_Key", yesterday['eq'], "clrMagenta",
                style=0, width=2,
                label=f"C3_EQ_Key : {f(yesterday['eq'])}")

        # C4 레벨
        elif cnum == 'C4':
            c3_eq        = prev2['eq']
            c3_high      = prev2['high']
            c3_low       = prev2['low']
            c3_upper_mid = (c3_high + c3_eq) / 2
            c3_lower_mid = (c3_eq + c3_low) / 2

            add("C3_High", c3_high, "clrLightCoral",
                style=2, width=1,
                label=f"C3_High : {f(c3_high)}")

            add("C3_Low", c3_low, "clrLightBlue",
                style=2, width=1,
                label=f"C3_Low : {f(c3_low)}")

            add("C3_EQ", c3_eq, "clrMagenta",
                style=0, width=2,
                label=f"C3_EQ : {f(c3_eq)}")

            if direction == 'up':
                add("C3_UpperMid", c3_upper_mid, "clrLimeGreen",
                    style=1, width=1,
                    label=f"C3_UpperMid : {f(c3_upper_mid)}")
            else:
                add("C3_LowerMid", c3_lower_mid, "clrOrangeRed",
                    style=1, width=1,
                    label=f"C3_LowerMid : {f(c3_lower_mid)}")

        return levels

    # --------------------------------
    # MQL5 코드 생성
    # --------------------------------
    def _generate_mql5(self, display_name: str, levels: list,
                       broker_name: str, dec: int,
                       yesterday, cnum: str) -> str:

        today_str = datetime.today().strftime('%Y-%m-%d')
        prefix    = self.OBJ_PREFIX

        # 레벨 오브젝트 생성 블록
        obj_blocks = ""
        for lv in levels:
            obj_name = f"{prefix}{display_name}_{lv['name']}"
            obj_blocks += f"""
   //--- {lv['name']}
   ObjectCreate(0, "{obj_name}", OBJ_HLINE, 0, 0, {lv['value']:.{dec}f});
   ObjectSetInteger(0, "{obj_name}", OBJPROP_COLOR,     {lv['color']});
   ObjectSetInteger(0, "{obj_name}", OBJPROP_STYLE,     {lv['style']});
   ObjectSetInteger(0, "{obj_name}", OBJPROP_WIDTH,     {lv['width']});
   ObjectSetString (0, "{obj_name}", OBJPROP_TEXT,      "{lv['label']}");
   ObjectSetInteger(0, "{obj_name}", OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, "{obj_name}", OBJPROP_BACK,       true);
"""

        return f"""//+------------------------------------------------------------------+
//|  {display_name} - Daily Briefing Lines                            |
//|  생성일 : {today_str}                                             |
//|  브로커 : {broker_name}                                           |
//|  캔들   : {cnum if cnum != "-" else "분류없음"}                   |
//|  생성툴 : TTrades Daily Briefing Tool                             |
//+------------------------------------------------------------------+
#property script_show_inputs

input bool DeleteExisting = true;
// true  : 기존 오브젝트 삭제 후 새로 그리기
// false : 기존 오브젝트 유지

//+------------------------------------------------------------------+
void OnStart()
{{
   //--- 기존 오브젝트 삭제
   if(DeleteExisting)
   {{
      int total = ObjectsTotal(0);
      for(int i = total - 1; i >= 0; i--)
      {{
         string name = ObjectName(0, i);
         if(StringFind(name, "{prefix}{display_name}_") == 0)
            ObjectDelete(0, name);
      }}
   }}

   //--- 레벨 그리기
{obj_blocks}

   ChartRedraw(0);
   Print("✅ {display_name} 레벨 완료 | {today_str} | {cnum}");
}}
//+------------------------------------------------------------------+
"""

    # --------------------------------
    # 삭제 전용 스크립트 생성
    # --------------------------------
    def build_delete_script(self, display_name: str = None) -> str:
        today_str  = datetime.today().strftime('%Y-%m-%d')
        prefix     = self.OBJ_PREFIX
        target_str = f"{prefix}{display_name}_" if display_name else prefix
        label      = display_name if display_name else "전체"

        code = f"""//+------------------------------------------------------------------+
//|  Delete Daily Briefing Lines ({label})                            |
//|  생성일 : {today_str}                                             |
//+------------------------------------------------------------------+

void OnStart()
{{
   int deleted = 0;
   int total   = ObjectsTotal(0);
   for(int i = total - 1; i >= 0; i--)
   {{
      string name = ObjectName(0, i);
      if(StringFind(name, "{target_str}") == 0)
      {{
         ObjectDelete(0, name);
         deleted++;
      }}
   }}
   ChartRedraw(0);
   Print("삭제 완료: ", deleted, "개 ({label})");
}}
//+------------------------------------------------------------------+
"""
        filename = f"Delete_{label}_{today_str}.mq5"
        filepath = os.path.join(SCRIPTS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        return filepath
