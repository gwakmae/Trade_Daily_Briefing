class LegendComponents:
    def legend_html(self) -> str:
        return f"""
<div class="legend">
<h3>📌 범례 및 분류 기준</h3>
<p>
<b>반전 캔들:</b> 최대꼬리 ≥ {self.fmt.rw}% AND 몸통 ≤ {self.fmt.rb}%<br>
<b>확장 캔들:</b> 몸통 ≥ {self.fmt.eb}% AND 위/아래꼬리 각각 ≤ {self.fmt.ew}%<br>
<b>C2:</b> 전일 반전캔들 &nbsp;|&nbsp;
<b>C3:</b> 전전일 반전 + 전일 확장 &nbsp;|&nbsp;
<b>C4:</b> 3일전 반전 + 전전일 확장 + 전일 확장<br>
<b>SwH:</b> 양쪽 {self.fmt.slb}캔들보다 고가 높음 &nbsp;|&nbsp;
<b>SwL:</b> 양쪽 {self.fmt.slb}캔들보다 저가 낮음<br>
<b>전주봉:</b> 전주 마감 기준 수치. 현재 진행 중인 이번 주봉은 제외.<br>
<b>1시간봉 파동:</b> 전일 5분봉을 1시간 단위로 리샘플링. KST 기준.
AS=아시아(07~15 KST) / EU=유럽(16~21 KST) / NY=뉴욕(22~06 KST).
</p>
</div>"""