from config import DECIMAL_PLACES
from core.mt5_connector import MT5Connector
from core.report_formatter import ReportFormatter

class ReportComponentsBase:
    def __init__(self, formatter: ReportFormatter = None):
        self.fmt = formatter or ReportFormatter()