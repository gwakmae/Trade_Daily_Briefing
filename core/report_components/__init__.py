from ._base import ReportComponentsBase
from ._charts import ChartComponents
from ._sections import SectionComponents
from ._card_builder import CardBuilder
from ._legend import LegendComponents

class ReportComponents(ReportComponentsBase, ChartComponents, SectionComponents, CardBuilder, LegendComponents):
    """기존 ReportComponents와 100% 동일한 인터페이스 제공"""
    pass

__all__ = ["ReportComponents"]