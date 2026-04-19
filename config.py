"""
Proxy Redirector — Configuration
يقرأ الإعدادات من data/config.json ويُنشئه بالقيم الافتراضية إذا لم يكن موجوداً.
التغييرات من الواجهة تُحفظ مباشرة في JSON.
"""

import json
import os

# ─── مسار ملف الإعدادات ───
_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "config.json"
)

# ──────────────────────────────────────────────
# القيم الافتراضية
# ──────────────────────────────────────────────
_DEFAULTS = {
    # Pool
    "MIN_ALIVE_POOL": 3,
    "BATCH_SIZE": 50,
    "RECHECK_INTERVAL_SECONDS": 60,

    # Retry
    "DEAD_RETRY_AFTER_SECONDS": 300,
    "MAX_CONSECUTIVE_FAILURES": 5,
    "BLACKLIST_AFTER_FAILURES": 15,
    "DEAD_RECHECK_BATCH": 10,

    # Check
    "CHECK_TIMEOUT_SECONDS": 8,
    "MAX_CONCURRENT_CHECKS": 50,
    "CHECK_URL": "http://httpbin.org/ip",
    "ANONYMITY_CHECK": True,

    # Server
    "LOCAL_HOST": "0.0.0.0",
    "LOCAL_PORT": 1080,
    "HTTP_PROXY_PORT": 8080,

    # Auth
    "AUTH_ENABLED": True,
    "AUTH_USERNAME": "admin",
    "AUTH_PASSWORD": "proxy2026",
    "AUTH_WHITELIST": [
        "192.168.100.",
        "192.168.1.",
        "192.168.0.",
        "127.0.0.1",
    ],

    # Failover
    "FAILOVER_MAX_RETRIES": 3,
    "FAILOVER_RETRY_DELAY": 1,

    # Files
    "PROXIES_FILE": "data/data.json",
    "STATUS_FILE": "data/proxies_status.json",
    "BLOCKLIST_FILE": "data/blocklist.json",

    # Ad Blocker
    "ADBLOCK_ENABLED": True,

    # Country Filter
    "COUNTRY_FILTER": "GLOBAL",        # ISO 2-letter code or GLOBAL
    "MAX_SPEED_MS": 0,                 # 0 = no limit, e.g. 200 = reject > 200ms

    # Scoring
    "SCORE_ALIVE": 50,
    "SCORE_SPEED_MAX": 25,
    "SCORE_RECENCY_MAX": 15,
    "SCORE_FAILURE_PENALTY": 5,
    "SCORE_SUCCESS_RATE_MAX": 10,
    "SPEED_THRESHOLD_MS": 500,

    # App Display
    "START_WITH_GUI": True,            # Always start GUI on launch
    "HIDE_CONSOLE": True,              # Hide terminal console visually
}


def _load_config() -> dict:
    """تحميل الإعدادات من JSON أو إنشاء الملف بالقيم الافتراضية."""
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # دمج: الافتراضي كقاعدة + المحفوظ فوقه
            merged = {**_DEFAULTS, **saved}
            return merged
        except (json.JSONDecodeError, IOError):
            pass

    # إنشاء الملف بالقيم الافتراضية
    os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(_DEFAULTS, f, indent=2, ensure_ascii=False)
    return dict(_DEFAULTS)


def save_config():
    """حفظ الإعدادات الحالية في JSON."""
    data = {}
    for key in _DEFAULTS:
        data[key] = globals().get(key, _DEFAULTS[key])

    os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_config(updates: dict) -> dict:
    """
    تحديث إعدادات محددة (من الواجهة).
    يُحدّث المتغيرات في الذاكرة ويحفظ في JSON.
    يعيد dict بالإعدادات المحدّثة.
    """
    changed = {}
    for key, value in updates.items():
        if key in _DEFAULTS:
            # تحويل النوع لضمان التوافق
            default_type = type(_DEFAULTS[key])
            try:
                if default_type == bool and isinstance(value, str):
                    value = value.lower() in ("true", "1", "yes")
                elif default_type == int and not isinstance(value, bool):
                    value = int(value)
                elif default_type == float:
                    value = float(value)
            except (ValueError, TypeError):
                continue

            globals()[key] = value
            changed[key] = value

    if changed:
        save_config()

    return changed


def get_all_config() -> dict:
    """إرجاع كل الإعدادات الحالية."""
    return {key: globals().get(key, _DEFAULTS[key]) for key in _DEFAULTS}


# ── تحميل الإعدادات وتعيينها كمتغيرات عامة ──
_config = _load_config()
for _key, _val in _config.items():
    globals()[_key] = _val

# ── Runtime-only (لا تُحفظ في JSON) ──
REAL_IP: str | None = None
