"""
Proxy Redirector — Proxy Analytics Engine
تتبع الأداء التاريخي للبروكسيات وتعلّم أيها الأفضل على مدار الزمن.
"""

import json
import os
import logging
import threading
from datetime import datetime, timezone
from collections import defaultdict

import config

logger = logging.getLogger("analytics")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ANALYTICS_FILE = os.path.join(_PROJECT_ROOT, "data", "analytics.json")
_MAX_SPEED_HISTORY = 50  # آخر 50 قراءة سرعة لكل بروكسي
_SAVE_INTERVAL = 20  # يحفظ كل 20 تسجيل


class ProxyAnalytics:
    """محرك تحليلات البروكسيات (Singleton)."""

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ProxyAnalytics":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._data: dict[str, dict] = {}
        self._records_since_save = 0
        self._load()

    # ── Persistence ──

    def _load(self):
        if os.path.exists(_ANALYTICS_FILE):
            try:
                with open(_ANALYTICS_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        os.makedirs(os.path.dirname(_ANALYTICS_FILE), exist_ok=True)
        try:
            with open(_ANALYTICS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False)
        except IOError as e:
            logger.error(f"[ANALYTICS] Save failed: {e}")

    # ── Recording ──

    def record_check(self, proxy_id: str, alive: bool, speed_ms: float | None, country: str = "??"):
        """تسجيل نتيجة فحص واحد."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        day = now.strftime("%Y-%m-%d")

        if proxy_id not in self._data:
            self._data[proxy_id] = {
                "total_checks": 0,
                "total_successes": 0,
                "total_failures": 0,
                "avg_speed_ms": 0,
                "min_speed_ms": None,
                "max_speed_ms": None,
                "speed_history": [],
                "uptime_pct": 0,
                "hourly_uptime": {},   # { "0": [checks, successes], ... }
                "daily_avg_speed": {},  # { "2026-04-19": [total_ms, count] }
                "reliability_score": 0,
                "first_seen": now.isoformat(),
                "last_seen": now.isoformat(),
                "country": country,
                "tags": [],
            }

        entry = self._data[proxy_id]
        entry["total_checks"] += 1
        entry["last_seen"] = now.isoformat()
        entry["country"] = country

        # Hourly tracking
        h_key = str(hour)
        if h_key not in entry["hourly_uptime"]:
            entry["hourly_uptime"][h_key] = [0, 0]
        entry["hourly_uptime"][h_key][0] += 1  # total checks this hour

        if alive:
            entry["total_successes"] += 1
            entry["hourly_uptime"][h_key][1] += 1  # successes this hour

            if speed_ms is not None:
                # Speed history
                entry["speed_history"].append(round(speed_ms, 1))
                if len(entry["speed_history"]) > _MAX_SPEED_HISTORY:
                    entry["speed_history"] = entry["speed_history"][-_MAX_SPEED_HISTORY:]

                # Min/Max
                if entry["min_speed_ms"] is None or speed_ms < entry["min_speed_ms"]:
                    entry["min_speed_ms"] = round(speed_ms, 1)
                if entry["max_speed_ms"] is None or speed_ms > entry["max_speed_ms"]:
                    entry["max_speed_ms"] = round(speed_ms, 1)

                # Running average
                speeds = entry["speed_history"]
                entry["avg_speed_ms"] = round(sum(speeds) / len(speeds), 1)

                # Daily speed
                if day not in entry["daily_avg_speed"]:
                    entry["daily_avg_speed"][day] = [0, 0]
                entry["daily_avg_speed"][day][0] += speed_ms
                entry["daily_avg_speed"][day][1] += 1

                # Keep only last 14 days
                if len(entry["daily_avg_speed"]) > 14:
                    keys = sorted(entry["daily_avg_speed"].keys())
                    for old_key in keys[:-14]:
                        del entry["daily_avg_speed"][old_key]
        else:
            entry["total_failures"] += 1

        # Uptime percentage
        if entry["total_checks"] > 0:
            entry["uptime_pct"] = round(
                100 * entry["total_successes"] / entry["total_checks"], 1
            )

        # Reliability score
        entry["reliability_score"] = self._calc_reliability(entry)

        # Auto-tag
        entry["tags"] = self._auto_tag(entry)

        # Periodic save
        self._records_since_save += 1
        if self._records_since_save >= _SAVE_INTERVAL:
            self._save()
            self._records_since_save = 0

    # ── Calculations ──

    def _calc_reliability(self, entry: dict) -> float:
        """حساب نقاط الموثوقية (0-100)."""
        score = 0.0

        # Uptime (40%)
        score += entry["uptime_pct"] * 0.4

        # Speed (30%) — faster = better
        avg = entry.get("avg_speed_ms", 0)
        if avg > 0:
            speed_score = max(0, 100 - (avg / 5))  # 500ms → 0, 0ms → 100
            score += speed_score * 0.3

        # Consistency (20%) — low variance = better
        history = entry.get("speed_history", [])
        if len(history) >= 3:
            mean = sum(history) / len(history)
            variance = sum((x - mean) ** 2 for x in history) / len(history)
            std_dev = variance ** 0.5
            cv = std_dev / mean if mean > 0 else 1  # coefficient of variation
            consistency = max(0, 100 - cv * 100)
            score += consistency * 0.2

        # Recency (10%)
        try:
            last = datetime.fromisoformat(entry["last_seen"])
            age_hours = (datetime.now(timezone.utc) - last).total_seconds() / 3600
            recency = max(0, 100 - age_hours * 4)  # 25h old → 0
            score += recency * 0.1
        except (ValueError, TypeError):
            pass

        return round(min(100, max(0, score)), 1)

    def _auto_tag(self, entry: dict) -> list[str]:
        """تصنيف تلقائي بناءً على الأداء."""
        tags = []
        avg = entry.get("avg_speed_ms", 0)
        uptime = entry.get("uptime_pct", 0)
        checks = entry.get("total_checks", 0)

        if checks < 3:
            return ["new"]

        if avg > 0 and avg < 150:
            tags.append("fast")
        elif avg > 500:
            tags.append("slow")

        if uptime >= 90:
            tags.append("stable")
        elif uptime < 50:
            tags.append("unreliable")

        if entry.get("reliability_score", 0) >= 80:
            tags.append("recommended")

        return tags

    # ── Queries ──

    def get_proxy_analytics(self, proxy_id: str) -> dict | None:
        """بيانات تحليلية لبروكسي واحد."""
        entry = self._data.get(proxy_id)
        if not entry:
            return None

        result = dict(entry)
        # Compute daily averages for display
        daily = {}
        for day, (total_ms, count) in entry.get("daily_avg_speed", {}).items():
            daily[day] = round(total_ms / count, 1) if count > 0 else 0
        result["daily_avg_speed_display"] = daily

        # Hourly uptime percentages
        hourly = {}
        for h, (checks, successes) in entry.get("hourly_uptime", {}).items():
            hourly[h] = round(100 * successes / checks, 1) if checks > 0 else 0
        result["hourly_uptime_display"] = hourly

        return result

    def get_top_proxies(self, n: int = 15, sort_by: str = "reliability_score") -> list[dict]:
        """أفضل N بروكسي حسب معيار محدد."""
        items = []
        for pid, entry in self._data.items():
            if entry.get("total_checks", 0) < 2:
                continue
            items.append({
                "id": pid,
                "country": entry.get("country", "??"),
                "avg_speed_ms": entry.get("avg_speed_ms", 0),
                "uptime_pct": entry.get("uptime_pct", 0),
                "reliability_score": entry.get("reliability_score", 0),
                "total_checks": entry.get("total_checks", 0),
                "tags": entry.get("tags", []),
            })

        reverse = True
        if sort_by == "avg_speed_ms":
            reverse = False  # lower is better
        items.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        return items[:n]

    def get_country_stats(self) -> list[dict]:
        """إحصائيات الأداء حسب البلد."""
        countries = defaultdict(lambda: {
            "count": 0, "total_speed": 0, "speed_samples": 0,
            "total_uptime": 0, "total_reliability": 0,
        })

        for pid, entry in self._data.items():
            c = entry.get("country", "??")
            countries[c]["count"] += 1
            if entry.get("avg_speed_ms", 0) > 0:
                countries[c]["total_speed"] += entry["avg_speed_ms"]
                countries[c]["speed_samples"] += 1
            countries[c]["total_uptime"] += entry.get("uptime_pct", 0)
            countries[c]["total_reliability"] += entry.get("reliability_score", 0)

        result = []
        for code, s in countries.items():
            n = s["count"]
            result.append({
                "country": code,
                "proxy_count": n,
                "avg_speed_ms": round(s["total_speed"] / s["speed_samples"], 1) if s["speed_samples"] > 0 else 0,
                "avg_uptime_pct": round(s["total_uptime"] / n, 1) if n > 0 else 0,
                "avg_reliability": round(s["total_reliability"] / n, 1) if n > 0 else 0,
            })

        result.sort(key=lambda x: x["avg_reliability"], reverse=True)
        return result

    def get_summary(self) -> dict:
        """ملخص عام للتحليلات."""
        total = len(self._data)
        if total == 0:
            return {
                "total_tracked": 0,
                "avg_speed": 0,
                "avg_uptime": 0,
                "best_proxy": None,
                "worst_proxy": None,
                "total_checks": 0,
            }

        speeds = [e["avg_speed_ms"] for e in self._data.values() if e.get("avg_speed_ms", 0) > 0]
        uptimes = [e["uptime_pct"] for e in self._data.values() if e.get("total_checks", 0) >= 2]
        total_checks = sum(e.get("total_checks", 0) for e in self._data.values())

        # Best & worst by reliability
        sorted_items = sorted(
            [(pid, e) for pid, e in self._data.items() if e.get("total_checks", 0) >= 2],
            key=lambda x: x[1].get("reliability_score", 0),
            reverse=True,
        )

        best = None
        worst = None
        if sorted_items:
            bp = sorted_items[0]
            best = {"id": bp[0], "score": bp[1]["reliability_score"], "speed": bp[1].get("avg_speed_ms", 0)}
            wp = sorted_items[-1]
            worst = {"id": wp[0], "score": wp[1]["reliability_score"], "speed": wp[1].get("avg_speed_ms", 0)}

        return {
            "total_tracked": total,
            "avg_speed": round(sum(speeds) / len(speeds), 1) if speeds else 0,
            "avg_uptime": round(sum(uptimes) / len(uptimes), 1) if uptimes else 0,
            "best_proxy": best,
            "worst_proxy": worst,
            "total_checks": total_checks,
        }

    def flush(self):
        """حفظ فوري."""
        self._save()
