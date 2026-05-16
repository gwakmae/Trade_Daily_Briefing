# config.py
# 브로커 설정, 종목 리스트, 캔들 분석 임계값 등 전역 설정
# 계정 정보는 .env 파일에서 로드 (GitHub 비공개)

import os
import json
import copy
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ================================
# 일봉 마감 기준 시간 (한국 시간)
# 07:00 이후 → 전일 봉 기준
# 07:00 이전 → 전전일 봉 기준
# 전 종목 동일 적용 (비트코인 포함)
# ================================
SESSION_CLOSE_HOUR = 7   # 한국 시간 07:00

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
# JPY 관련 종목 전체 제외 (USDJPY, GBPJPY, EURJPY, AUDJPY)
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
        "QQQUSDT": {  # ★ 추가: 나스닥 100 추종 (US100 옆 배치)
            "Binance": "QQQUSDT",
        },
        "US500": {
            "FP Markets":   "US500",
            "Zero Markets": "US500",
        },
        "GER40": {
            "FP Markets":   "GER40",
            "Zero Markets": "GER40",
        },
        "FRA40": {
            "FP Markets":   "FRA40",
            "Zero Markets": "FRA40",
        },
        "UK100": {
            "FP Markets":   "UK100",
            "Zero Markets": "UK100",
        },
        "KS200": {
            "Zero Markets": "KS200",
        },
        "EWYUSDT": {  # ★ 추가: 코스피 추종 (KS200 옆 배치)
            "Binance": "EWYUSDT",
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
        "ETHUSDT": {  # ★ 추가: 이더리움 (BTCUSD 옆 배치)
            "Binance": "ETHUSDT",
        },
    },
    "포렉스 메이저": {
        "EURUSD": {
            "FP Markets":   "EURUSD.r",
            "Zero Markets": "EURUSD.r",
        },
        "GBPUSD": {
            "FP Markets":   "GBPUSD.r",
            "Zero Markets": "GBPUSD.r",
        },
        # USDJPY 제외
        "AUDUSD": {
            "FP Markets":   "AUDUSD.r",
            "Zero Markets": "AUDUSD.r",
        },
        "NZDUSD": {
            "FP Markets":   "NZDUSD.r",
            "Zero Markets": "NZDUSD.r",
        },
        "USDCAD": {
            "FP Markets":   "USDCAD.r",
            "Zero Markets": "USDCAD.r",
        },
        "USDCHF": {
            "FP Markets":   "USDCHF.r",
            "Zero Markets": "USDCHF.r",
        },
    },
    "포렉스 크로스": {
        # GBPJPY, EURJPY, AUDJPY 제외
        "EURGBP": {
            "FP Markets":   "EURGBP.r",
            "Zero Markets": "EURGBP.r",
        },
        "EURCHF": {
            "FP Markets":   "EURCHF.r",
            "Zero Markets": "EURCHF.r",
        },
        "GBPAUD": {
            "FP Markets":   "GBPAUD.r",
            "Zero Markets": "GBPAUD.r",
        },
    },
}

# 주말에도 거래되는 종목
WEEKEND_SYMBOLS = ["BTCUSD"]

# Binance 소스는 MQL5 스크립트 생성 비활성화
BINANCE_NO_SCRIPT = True

# 소수점 자리수
# JPY 종목 제외, US500 추가
DECIMAL_PLACES = {
    "HK50":   0,
    "US100":  1,
    "QQQUSDT": 2,  # ★ 추가
    "US500":  2,
    "GER40":  1,
    "FRA40":  1,
    "UK100":  1,
    "KS200":  2,
    "EWYUSDT": 3,  # ★ 추가

    "XAUUSD": 2,
    "XTIUSD": 2,

    "BTCUSD": 0,
    "ETHUSDT": 2,  # ★ 추가

    "EURUSD": 5,
    "GBPUSD": 5,
    # USDJPY 제외
    "AUDUSD": 5,
    "NZDUSD": 5,
    "USDCAD": 5,
    "USDCHF": 5,

    # GBPJPY, EURJPY, AUDJPY 제외
    "EURGBP": 5,
    "EURCHF": 5,
    "GBPAUD": 5,
}

# ★ Binance 선물 API 분기용 상수 (EWY, QQQ는 USDS-M 선물)
BINANCE_FUTURES_SYMBOLS = {"EWYUSDT", "QQQUSDT"}

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
# 설정 파일
# settings.json 에 저장
# ================================
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

_DEFAULT_SETTINGS = {
    # 브로커별 MT5 Scripts 복사 경로
    "mt5_scripts_paths": {
        "FP Markets":   "",
        "Zero Markets": "",
        "Deriv":        "",
    },

    # 종목 선택 상태 저장
    # report/script 탭 각각 별도 저장
    "symbol_selections": {
        "report": {},
        "script": {},
    },
}


def _deep_merge(default: dict, data: dict) -> dict:
    """
    settings.json 에 새 설정 항목이 추가되어도
    기존 settings.json 을 유지하면서 기본값을 병합
    """
    result = copy.deepcopy(default)

    if not isinstance(data, dict):
        return result

    for key, value in data.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return _deep_merge(_DEFAULT_SETTINGS, data)
        except Exception:
            pass

    return copy.deepcopy(_DEFAULT_SETTINGS)


def save_settings(data: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)