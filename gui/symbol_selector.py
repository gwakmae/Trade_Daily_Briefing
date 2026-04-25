# gui/symbol_selector.py
# 종목 체크박스 선택 공통 위젯

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QPushButton, QGroupBox,
    QScrollArea, QLabel, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import SYMBOLS, WEEKEND_SYMBOLS, BROKERS


class SymbolSelector(QWidget):

    def __init__(self, show_broker=True, parent=None):
        super().__init__(parent)
        self.show_broker   = show_broker
        self.checkboxes    = {}   # display_name → QCheckBox
        self.broker_combos = {}   # display_name → QComboBox
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 빠른 선택 버튼
        quick_box    = QGroupBox("빠른 선택")
        quick_layout = QHBoxLayout(quick_box)

        btn_all     = QPushButton("전체 선택")
        btn_none    = QPushButton("전체 해제")
        btn_weekend = QPushButton("주말 (BTC)")
        btn_index   = QPushButton("지수만")
        btn_forex   = QPushButton("포렉스만")

        for btn in [btn_all, btn_none, btn_weekend, btn_index, btn_forex]:
            btn.setFixedHeight(30)
            quick_layout.addWidget(btn)

        btn_all.clicked.connect(self.select_all)
        btn_none.clicked.connect(self.deselect_all)
        btn_weekend.clicked.connect(self.select_weekend)
        btn_index.clicked.connect(self.select_index)
        btn_forex.clicked.connect(self.select_forex)

        layout.addWidget(quick_box)

        # 스크롤 영역
        scroll        = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)

        for section, symbols_dict in SYMBOLS.items():
            group        = QGroupBox(section)
            group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(4)

            for display_name, broker_map in symbols_dict.items():
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)

                cb = QCheckBox(display_name)
                cb.setChecked(True)
                cb.setFont(QFont("Segoe UI", 9))
                self.checkboxes[display_name] = cb
                row_layout.addWidget(cb)

                if self.show_broker:
                    available_brokers = list(broker_map.keys())

                    if len(available_brokers) >= 1:
                        combo = QComboBox()
                        combo.addItems(available_brokers)
                        combo.setFixedWidth(140)
                        combo.setFont(QFont("Segoe UI", 8))
                        self.broker_combos[display_name] = combo
                        row_layout.addWidget(QLabel("브로커:"))
                        row_layout.addWidget(combo)

                        # 브로커 변경 시 활성화 상태 업데이트
                        combo.currentTextChanged.connect(
                            lambda text, dn=display_name: self._on_broker_changed(dn, text)
                        )

                row_layout.addStretch()
                group_layout.addWidget(row_widget)

            scroll_layout.addWidget(group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    # --------------------------------
    # 브로커 변경 시 비활성화 처리
    # --------------------------------
    def _on_broker_changed(self, display_name: str, broker_name: str):
        cb          = self.checkboxes.get(display_name)
        broker_map  = self._get_broker_map(display_name)
        if cb is None or broker_map is None:
            return

        supported = broker_name in broker_map
        cb.setEnabled(supported)
        if not supported:
            cb.setChecked(False)
            cb.setToolTip(f"{broker_name} 에서 지원하지 않는 종목입니다.")
        else:
            cb.setToolTip("")

    def _get_broker_map(self, display_name: str) -> dict | None:
        for section in SYMBOLS.values():
            if display_name in section:
                return section[display_name]
        return None

    # --------------------------------
    # 전체 브로커 변경 (리포트탭 글로벌 브로커 선택 시 사용)
    # --------------------------------
    def set_global_broker(self, broker_name: str):
        for display_name, combo in self.broker_combos.items():
            idx = combo.findText(broker_name)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            # 지원 안 하는 종목 비활성화
            self._on_broker_changed(display_name, combo.currentText())

    # --------------------------------
    # 빠른 선택 메서드
    # --------------------------------
    def select_all(self):
        for display_name, cb in self.checkboxes.items():
            broker_map = self._get_broker_map(display_name)
            combo      = self.broker_combos.get(display_name)
            broker     = combo.currentText() if combo else None
            if broker and broker_map and broker not in broker_map:
                continue   # 지원 안 하는 종목은 건너뜀
            cb.setChecked(True)

    def deselect_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def select_weekend(self):
        self.deselect_all()
        for name in WEEKEND_SYMBOLS:
            if name in self.checkboxes:
                self.checkboxes[name].setChecked(True)

    def select_index(self):
        self.deselect_all()
        for name in SYMBOLS.get("지수", {}).keys():
            if name in self.checkboxes:
                cb         = self.checkboxes[name]
                broker_map = self._get_broker_map(name)
                combo      = self.broker_combos.get(name)
                broker     = combo.currentText() if combo else None
                if broker and broker_map and broker not in broker_map:
                    continue
                cb.setChecked(True)

    def select_forex(self):
        self.deselect_all()
        for section in ["포렉스 메이저", "포렉스 크로스"]:
            for name in SYMBOLS.get(section, {}).keys():
                if name in self.checkboxes:
                    self.checkboxes[name].setChecked(True)

    # --------------------------------
    # 선택된 종목 반환
    # --------------------------------
    def get_selected(self) -> list[dict]:
        from config import DEFAULT_BROKER
        result = []
        for display_name, cb in self.checkboxes.items():
            if cb.isChecked() and cb.isEnabled():
                broker = DEFAULT_BROKER
                if display_name in self.broker_combos:
                    broker = self.broker_combos[display_name].currentText()
                result.append({
                    "display_name": display_name,
                    "broker":       broker,
                })
        return result
