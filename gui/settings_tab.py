# gui/settings_tab.py
# 설정 탭

import os
import subprocess
import importlib

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSpinBox, QGroupBox, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont
from config import CANDLE_THRESHOLDS, BROKERS, BASE_DIR, load_settings, save_settings


class SettingsTab(QWidget):

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # --------------------------------
        # 1. config.py 편집
        # --------------------------------
        config_group  = QGroupBox("브로커 계정 설정 (config.py 직접 편집)")
        config_group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        config_layout = QHBoxLayout(config_group)

        btn_open = QPushButton("📝 메모장으로 config.py 열기")
        btn_open.setFixedHeight(34)
        btn_open.clicked.connect(self._open_config)
        config_layout.addWidget(btn_open)

        btn_reload = QPushButton("🔄 새로고침 (변경사항 적용)")
        btn_reload.setFixedHeight(34)
        btn_reload.clicked.connect(self._reload_config)
        config_layout.addWidget(btn_reload)

        config_layout.addStretch()
        layout.addWidget(config_group)

        # --------------------------------
        # 2. 캔들 분석 임계값
        # --------------------------------
        threshold_group = QGroupBox("캔들 분석 임계값")
        threshold_group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        form = QFormLayout(threshold_group)

        self.spins = {}
        labels = {
            "reversal_wick":  "반전 캔들 꼬리 기준 (%)",
            "reversal_body":  "반전 캔들 몸통 기준 (%)",
            "expansion_body": "확장 캔들 몸통 기준 (%)",
            "expansion_wick": "확장 캔들 꼬리 기준 (%)",
            "swing_lookback": "스윙 포인트 양쪽 캔들 수",
            "data_count":     "MT5 데이터 수집 캔들 수",
        }
        for key, label in labels.items():
            spin = QSpinBox()
            spin.setRange(1, 200)
            spin.setValue(CANDLE_THRESHOLDS[key])
            spin.setFixedWidth(80)
            self.spins[key] = spin
            form.addRow(label, spin)

        layout.addWidget(threshold_group)

        btn_save = QPushButton("💾 임계값 저장 (현재 세션 적용)")
        btn_save.setFixedHeight(34)
        btn_save.clicked.connect(self._save_thresholds)
        layout.addWidget(btn_save)

        self.threshold_label = QLabel("")
        layout.addWidget(self.threshold_label)

        # --------------------------------
        # 3. MT5 Scripts 복사 경로
        # --------------------------------
        path_group  = QGroupBox("브로커별 MT5 Scripts 복사 경로")
        path_group.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        path_layout = QVBoxLayout(path_group)

        settings          = load_settings()
        self.path_edits   = {}
        mt5_scripts_paths = settings.get("mt5_scripts_paths", {})

        for broker_name, cfg in BROKERS.items():
            if cfg.get("type") != "mt5":
                continue

            row        = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 4, 0, 4)

            lbl = QLabel(f"{broker_name}:")
            lbl.setFixedWidth(110)
            row_layout.addWidget(lbl)

            edit = QLineEdit()
            edit.setPlaceholderText("MT5 Scripts 폴더 경로 입력 또는 찾아보기...")
            edit.setText(mt5_scripts_paths.get(broker_name, ""))
            edit.setFont(QFont("Consolas", 8))
            self.path_edits[broker_name] = edit
            row_layout.addWidget(edit)

            btn_browse = QPushButton("찾아보기")
            btn_browse.setFixedWidth(80)
            btn_browse.setFixedHeight(28)
            btn_browse.clicked.connect(
                lambda checked, bn=broker_name: self._browse_path(bn)
            )
            row_layout.addWidget(btn_browse)
            path_layout.addWidget(row)

        btn_save_paths = QPushButton("💾 경로 저장")
        btn_save_paths.setFixedHeight(34)
        btn_save_paths.clicked.connect(self._save_paths)
        path_layout.addWidget(btn_save_paths)

        self.path_label = QLabel("")
        path_layout.addWidget(self.path_label)

        layout.addWidget(path_group)
        layout.addStretch()

    # --------------------------------
    # config.py 메모장 열기
    # --------------------------------
    def _open_config(self):
        config_path = os.path.join(BASE_DIR, "config.py")
        try:
            subprocess.Popen(["notepad.exe", config_path])
        except Exception as e:
            QMessageBox.critical(self, "오류", f"메모장 열기 실패:\n{e}")

    # --------------------------------
    # config.py 새로고침
    # --------------------------------
    def _reload_config(self):
        try:
            import config
            importlib.reload(config)

            # 임계값 스핀박스 업데이트
            for key, spin in self.spins.items():
                spin.setValue(config.CANDLE_THRESHOLDS[key])

            # 경로 에디트 업데이트
            settings = config.load_settings()
            paths    = settings.get("mt5_scripts_paths", {})
            for broker_name, edit in self.path_edits.items():
                edit.setText(paths.get(broker_name, ""))

            self.threshold_label.setText("✅ config.py 새로고침 완료")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"새로고침 실패:\n{e}")

    # --------------------------------
    # 임계값 저장 (현재 세션)
    # --------------------------------
    def _save_thresholds(self):
        for key, spin in self.spins.items():
            CANDLE_THRESHOLDS[key] = spin.value()
        self.threshold_label.setText("✅ 저장됨 (현재 세션에만 적용, 영구 저장은 config.py 수정)")

    # --------------------------------
    # 복사 경로 찾아보기
    # --------------------------------
    def _browse_path(self, broker_name: str):
        folder = QFileDialog.getExistingDirectory(
            self, f"{broker_name} MT5 Scripts 폴더 선택"
        )
        if folder:
            self.path_edits[broker_name].setText(folder)

    # --------------------------------
    # 복사 경로 저장 (settings.json)
    # --------------------------------
    def _save_paths(self):
        settings = load_settings()
        paths    = {}
        for broker_name, edit in self.path_edits.items():
            paths[broker_name] = edit.text().strip()
        settings["mt5_scripts_paths"] = paths
        save_settings(settings)
        self.path_label.setText("✅ 경로 저장 완료 (settings.json)")
