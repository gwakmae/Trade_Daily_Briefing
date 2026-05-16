# core/script_mql5_generator.py
# ScriptBuilder 의 MQL5 코드 문자열 생성 로직 분리

from datetime import datetime


class MQL5Generator:
    """수집된 레벨 정보를 MQL5 스크립트 코드 문자열로 변환"""

    OBJ_PREFIX = "TB_"

    def generate(
        self,
        display_name: str,
        levels: list[dict],
        broker_name: str,
        dec: int,
        cnum: str,
        expected_symbol: str,
    ) -> str:
        """완성된 MQL5 코드 문자열 반환"""
        today_str = datetime.today().strftime('%Y-%m-%d')
        prefix    = self.OBJ_PREFIX

        # ── 레벨 오브젝트 생성 블록 ──
        obj_blocks = self._build_object_blocks(display_name, levels, dec, prefix)

        return f"""//+------------------------------------------------------------------+
//|  {display_name} - Daily & Weekly Briefing Lines                   |
//|  생성일 : {today_str}                                             |
//|  브로커 : {broker_name}                                           |
//|  실제심볼 : {expected_symbol}                                     |
//|  캔들   : {cnum if cnum != "-" else "분류없음"}                   |
//|  생성툴 : TTrades Daily Briefing Tool                             |
//+------------------------------------------------------------------+
#property script_show_inputs

input bool DeleteExisting = true;
// true  : 기존 오브젝트 삭제 후 새로 그리기
// false : 기존 오브젝트 유지

input bool RequireMatchingSymbol = true;
// true  : 현재 차트 심볼이 실제심볼과 다르면 실행 중단
// false : 심볼이 달라도 강제로 선 그리기

//+------------------------------------------------------------------+
void OnStart()
{{
   string expected_symbol = "{expected_symbol}";

   //--- 현재 차트 심볼 검증
   if(RequireMatchingSymbol && _Symbol != expected_symbol)
   {{
      Alert(
         "심볼 불일치: 이 스크립트는 ",
         expected_symbol,
         " 차트용입니다. 현재 차트: ",
         _Symbol
      );

      Print(
         "심볼 불일치. Expected=",
         expected_symbol,
         " / Current=",
         _Symbol,
         " / 실행 중단"
      );

      return;
   }}

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

   Print(
      "✅ {display_name} 일봉/전주봉 레벨 완료 | ",
      "{today_str}",
      " | ",
      "{cnum}",
      " | ChartSymbol=",
      _Symbol
   );
}}
//+------------------------------------------------------------------+
"""

    def _build_object_blocks(
        self,
        display_name: str,
        levels: list[dict],
        dec: int,
        prefix: str,
    ) -> str:
        """오브젝트 생성 블록 문자열 생성"""
        blocks = ""

        for lv in levels:
            obj_name = f"{prefix}{display_name}_{lv['name']}"
            group    = lv.get("group", "daily")

            if group == "weekly":
                comment = f"전주봉 - {lv['name']}"
            else:
                comment = f"일봉 - {lv['name']}"

            blocks += f"""
   //--- {comment}
   ObjectCreate(0, "{obj_name}", OBJ_HLINE, 0, 0, {lv['value']:.{dec}f});
   ObjectSetInteger(0, "{obj_name}", OBJPROP_COLOR,      {lv['color']});
   ObjectSetInteger(0, "{obj_name}", OBJPROP_STYLE,      {lv['style']});
   ObjectSetInteger(0, "{obj_name}", OBJPROP_WIDTH,      {lv['width']});
   ObjectSetString (0, "{obj_name}", OBJPROP_TEXT,       "{lv['label']}");
   ObjectSetInteger(0, "{obj_name}", OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, "{obj_name}", OBJPROP_BACK,       true);
"""
        return blocks

    def generate_delete_script(
        self,
        display_name: str = None,
    ) -> str:
        """삭제 전용 스크립트 코드 문자열 반환"""
        today_str  = datetime.today().strftime('%Y-%m-%d')
        prefix     = self.OBJ_PREFIX
        target_str = f"{prefix}{display_name}_" if display_name else prefix
        label      = display_name if display_name else "전체"

        return f"""//+------------------------------------------------------------------+
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