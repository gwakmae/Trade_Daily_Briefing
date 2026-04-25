# config.py
# 브로커 설정, 종목 리스트, 캔들 분석 임계값 등 전역 설정
# 계정 정보는 .env 파일에서 로드 (GitHub 비공개)

import os
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ================================
# 브로커 설정
# ================================
BROKERS = {
    "FP Markets": {
        "login":    int(os.getenv("FP_LOGIN", "0")),
        "password": os.getenv("FP_PASSWORD", ""),
        "server":   os.getenv("FP_SERVER", ""),
        "path":     os.getenv("FP_PATH", ""),
        "type":     "mt5",
    },
    "Zero Markets": {
        "login":    int(os.getenv("ZERO_LOGIN", "0")),
        "password": os.getenv("ZERO_PASSWORD", ""),
        "server":   os.getenv("ZERO_SERVER", ""),
        "path":     os.getenv("ZERO_PATH", ""),
        "type":     "mt5",
    },
    "Deriv": {
        "login":    int(os.getenv("DERIV_LOGIN", "0")),
        "password": os.getenv("DERIV_PASSWORD", ""),
        "server":   os.getenv("DERIV_SERVER", ""),
        "path":     os.getenv("DERIV_PATH", ""),
        "type":     "mt5",
    },
    "Binance": {
        "type":    "binance",
        "api_url": "https://api.binance.com/api/v3/klines",
    },
}

# 기본 브로커
DEFAULT_BROKER = "FP Markets"

# ================================
# 종목 설정
# ================================
SYMBOLS = {
    "지수": {
        "HK50": {
            "FP Markets":   "HK50",
            "Zero Markets": "HK50",
        },
        "US100": {
            "FP Markets":   "US100",
            "Zero Markets": "US100",
        },
        "KS200": {
            "Zero Markets": "KS200",
            # FP Markets 미지원 → 회색 비활성화
        },
    },
    "원자재": {
        "XAUUSD": {
            "FP Markets":   "XAUUSD.r",
            "Zero Markets": "XAUUSD.r",
        },
        "XTIUSD": {
            "FP Markets":   "XTIUSD",
            "Zero Markets": "XTIUSD",
        },
    },
    "암호화폐": {
        "BTCUSD": {
            "FP Markets":   "BTCUSD",
            "Zero Markets": "BTCUSD",
            "Deriv":        "BTCUSD",
            "Binance":      "BTCUSDT",
        },
    },
    "포렉스 메이저": {
        "EURUSD": {"FP Markets": "EURUSD.r", "Zero Markets": "EURUSD.r"},
        "GBPUSD": {"FP Markets": "GBPUSD.r", "Zero Markets": "GBPUSD.r"},
        "USDJPY": {"FP Markets": "USDJPY.r", "Zero Markets": "USDJPY.r"},
        "AUDUSD": {"FP Markets": "AUDUSD.r", "Zero Markets": "AUDUSD.r"},
        "USDCAD": {"FP Markets": "USDCAD.r", "Zero Markets": "USDCAD.r"},
        "USDCHF": {"FP Markets": "USDCHF.r", "Zero Markets": "USDCHF.r"},
    },
    "포렉스 크로스": {
        "GBPJPY": {"FP Markets": "GBPJPY.r", "Zero Markets": "GBPJPY.r"},
        "EURJPY": {"FP Markets": "EURJPY.r", "Zero Markets": "EURJPY.r"},
        "AUDJPY": {"FP Markets": "AUDJPY.r", "Zero Markets": "AUDJPY.r"},
        "EURGBP": {"FP Markets": "EURGBP.r", "Zero Markets": "EURGBP.r"},
    },
}

# 주말에도 거래되는 종목
WEEKEND_SYMBOLS = ["BTCUSD"]

# Binance 소스는 MQL5 스크립트 생성 비활성화
BINANCE_NO_SCRIPT = True

# 소수점 자리수
DECIMAL_PLACES = {
    "HK50":   0,
    "US100":  1,
    "KS200":  2,
    "XAUUSD": 2,
    "XTIUSD": 2,
    "BTCUSD": 0,
    "EURUSD": 5,
    "GBPUSD": 5,
    "USDJPY": 3,
    "AUDUSD": 5,
    "USDCAD": 5,
    "USDCHF": 5,
    "GBPJPY": 3,
    "EURJPY": 3,
    "AUDJPY": 3,
    "EURGBP": 5,
}

# ================================
# 캔들 분석 임계값
# ================================
CANDLE_THRESHOLDS = {
    "reversal_wick":  40,
    "reversal_body":  30,
    "expansion_body": 60,
    "expansion_wick": 20,
    "swing_lookback":  2,
    "data_count":     30,
}

# ================================
# 경로 설정
# ================================
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")
SCRIPTS_DIR = os.path.join(OUTPUT_DIR, "scripts")
HISTORY_DIR = os.path.join(BASE_DIR, "history")
LOG_FILE    = os.path.join(HISTORY_DIR, "log.json")

for _dir in [OUTPUT_DIR, REPORTS_DIR, SCRIPTS_DIR, HISTORY_DIR]:
    os.makedirs(_dir, exist_ok=True)

# ================================
# 브로커별 MT5 Scripts 복사 경로
# settings.json 에 저장 (GitHub 비공개)
# ================================
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

_DEFAULT_SETTINGS = {
    "mt5_scripts_paths": {
        "FP Markets":   "",
        "Zero Markets": "",
        "Deriv":        "",
    }
}

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in _DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    return dict(_DEFAULT_SETTINGS)

def save_settings(data: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
