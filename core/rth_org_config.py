# core/rth_org_config.py
# RTH ORG 심볼 설정 및 상수
#
# 각 심볼은 다음 정보를 포함:
#   - rth_open  : 서버 시간 (h, m) — RTH Open
#   - rth_close : 서버 시간 (h, m) — RTH Close (24 이상이면 익일)
#   - dst_aware : 미국 DST 적용 여부 (True 면 비DST 시 +1시간 보정)
#   - lunch     : 런치브레이크 ((h, m), (h, m)) 또는 None
#   - night     : 야간세션  ((h, m), (h, m)) 또는 None
#   - min_gap   : 최소 갭 필터 (포인트)
#   - decimals  : 가격 표시 소수점 자리수
#   - size_bins / size_labels / fill_stats : 갭 크기 분류 및 통계

from zoneinfo import ZoneInfo

SERVER_TZ = ZoneInfo("Etc/GMT-3")   # 서버 = UTC+3 (Zero / FP 공통)


RTH_ORG_SYMBOLS = {

    # ──────────────────────────────────────────────
    # 미국 지수 (FP Markets)
    # 서버(UTC+3) 기준
    # DST 시:    16:30 ~ 23:15
    # 비DST 시:  17:30 ~ 익일 00:15
    # ──────────────────────────────────────────────
    "US100": {
        "rth_open":  (16, 30),
        "rth_close": (23, 15),
        "dst_aware": True,
        "lunch":     None,
        "night":     None,

        "min_gap":     5.0,
        "decimals":    1,
        "size_bins":   [5, 30, 100, 200, 99999],
        "size_labels": ["소형(5~30)", "중형(30~100)",
                        "대형(100~200)", "초대형(200+)"],
        "fill_stats": {
            "소형(5~30)":    {"fill_50": 100.0, "fill_100": 85.2},
            "중형(30~100)":  {"fill_50": 87.2,  "fill_100": 74.5},
            "대형(100~200)": {"fill_50": 69.0,  "fill_100": 34.5},
            "초대형(200+)":  {"fill_50": 51.5,  "fill_100": 27.3},
        },
        "overall_fill_50":  77.2,
        "overall_fill_100": 56.6,
        "up_fill_50":       71.6,
        "up_fill_100":      51.4,
        "down_fill_50":     83.9,
        "down_fill_100":    62.9,
    },

    "US500": {
        "rth_open":  (16, 30),
        "rth_close": (23, 15),
        "dst_aware": True,
        "lunch":     None,
        "night":     None,

        "min_gap":     0.5,
        "decimals":    2,
        "size_bins":   [0.5, 10, 30, 70, 99999],
        "size_labels": ["소형(0.5~10)", "중형(10~30)",
                        "대형(30~70)",  "초대형(70+)"],
        "fill_stats": {
            "소형(0.5~10)": {"fill_50": 95.3, "fill_100": 90.7},
            "중형(10~30)":  {"fill_50": 75.5, "fill_100": 52.8},
            "대형(30~70)":  {"fill_50": 50.0, "fill_100": 25.0},
            "초대형(70+)":  {"fill_50": 66.7, "fill_100": 44.4},
        },
        "overall_fill_50":  75.2,
        "overall_fill_100": 57.7,
        "up_fill_50":       72.2,
        "up_fill_100":      52.8,
        "down_fill_50":     78.5,
        "down_fill_100":    63.1,
    },

    # ──────────────────────────────────────────────
    # 코스피200 (Zero Markets)
    # KST 08:45 ~ 15:30 (DST 없음)
    # 서버(UTC+3) = KST(UTC+9) - 6h
    #   08:45 → 02:45
    #   15:30 → 09:30 (마감 봉 close = 09:25 봉)
    # 야간 세션: KST 18:10 ~ 익일 06:00
    # ──────────────────────────────────────────────
    "KS200": {
        "rth_open":  (2, 45),
        "rth_close": (9, 25),
        "dst_aware": False,
        "lunch":     None,
        "night":     ((12, 10), (24, 0)),   # 24=익일 00:00

        "min_gap":     1.0,
        "decimals":    2,
        "size_bins":   [1, 5, 15, 30, 99999],
        "size_labels": ["소형(1~5)", "중형(5~15)",
                        "대형(15~30)", "초대형(30+)"],
        "fill_stats": {
            "소형(1~5)":   {"fill_50": 56.0, "fill_100": 39.0},
            "중형(5~15)":  {"fill_50": 45.0, "fill_100": 26.0},
            "대형(15~30)": {"fill_50": 40.0, "fill_100": 20.0},
            "초대형(30+)": {"fill_50": 22.0, "fill_100": 22.0},
        },
        "overall_fill_50":  50.0,
        "overall_fill_100": 35.0,
        "up_fill_50":       50.0,
        "up_fill_100":      34.0,
        "down_fill_50":     62.0,
        "down_fill_100":    44.0,

        # 야간 세션 단독 채움 (참고용)
        "night_fill_50":    51.0,
        "night_fill_100":   43.0,
    },

    # ──────────────────────────────────────────────
    # 항셍 (Zero Markets)
    # HKT 09:15 ~ 16:30 (DST 없음)
    # 서버(UTC+3) = HKT(UTC+8) - 5h
    #   09:15 → 04:15
    #   16:30 → 11:30
    # 런치브레이크: HKT 12:00~13:00 = 서버 07:00~08:00
    # ──────────────────────────────────────────────
    "HK50": {
        "rth_open":  (4, 15),
        "rth_close": (11, 30),
        "dst_aware": False,
        "lunch":     ((7, 0), (8, 0)),
        "night":     None,

        "min_gap":     50.0,
        "decimals":    0,
        "size_bins":   [50, 150, 400, 800, 99999],
        "size_labels": ["소형(50~150)",  "중형(150~400)",
                        "대형(400~800)", "초대형(800+)"],
        "fill_stats": {
            "소형(50~150)":  {"fill_50": 78.0, "fill_100": 61.0},
            "중형(150~400)": {"fill_50": 42.0, "fill_100": 12.0},
            "대형(400~800)": {"fill_50": 20.0, "fill_100":  0.0},
            "초대형(800+)":  {"fill_50": 10.0, "fill_100":  0.0},
        },
        "overall_fill_50":  60.0,
        "overall_fill_100": 40.0,
        "up_fill_50":       67.0,
        "up_fill_100":      45.0,
        "down_fill_50":     78.0,
        "down_fill_100":    61.0,
    },
}


# ──────────────────────────────────────────────
# 심볼별 기본 브로커 매핑
# (morning_worker / facade 에서 자동 그룹핑용)
# ──────────────────────────────────────────────
DEFAULT_BROKER_BY_SYMBOL = {
    "US100": "FP Markets",
    "US500": "FP Markets",
    "KS200": "Zero Markets",
    "HK50":  "Zero Markets",
}
