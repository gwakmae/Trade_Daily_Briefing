# core/history_manager.py
import json
import os
from datetime import datetime
from config import LOG_FILE


class HistoryManager:

    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        # 파일이 없거나 비어있으면 빈 배열로 초기화
        if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _load(self) -> list:
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            # 파싱 실패 시 파일 초기화 후 빈 배열 반환
            self._ensure_file()
            return []

    def _save(self, data: list):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, action: str, symbols: list, broker: str,
            output_path: str = "", memo: str = ""):
        data = self._load()
        entry = {
            "timestamp":   datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "action":      action,
            "symbols":     symbols,
            "broker":      broker,
            "output_path": output_path,
            "memo":        memo,
        }
        data.append(entry)
        self._save(data)

    def get_all(self) -> list:
        return self._load()

    def get_recent(self, n: int = 20) -> list:
        data = self._load()
        return data[-n:]

    def get_by_action(self, action: str) -> list:
        return [r for r in self._load() if r['action'] == action]

    def get_by_symbol(self, symbol: str) -> list:
        return [r for r in self._load() if symbol in r['symbols']]
