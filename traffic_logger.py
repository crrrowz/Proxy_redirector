"""
Proxy Redirector — Traffic Logger
تتبع جميع الطلبات المارة عبر البروكسي (SOCKS5 + HTTP)
يحفظ آخر N طلب في الذاكرة + ملف لوج

البيانات المسجلة لكل طلب:
  - الوقت
  - IP العميل
  - البروتوكول (SOCKS5 / HTTP)
  - الهدف (host:port)
  - الطريقة (CONNECT / GET / POST ...)
  - الحالة (success / failed / blocked)
  - حجم البيانات المنقولة (تقريبي)
"""

import json
import os
import logging
from datetime import datetime, timezone
from collections import deque
from typing import Optional

import config

logger = logging.getLogger("traffic")

# أقصى عدد طلبات محفوظة في الذاكرة
MAX_MEMORY_ENTRIES = 500

# ملف اللوج
TRAFFIC_LOG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "traffic_log.json",
)


class TrafficLogger:
    """مسجّل حركة المرور — يحفظ في الذاكرة + ملف."""

    _instance: Optional["TrafficLogger"] = None

    def __init__(self):
        self._entries: deque[dict] = deque(maxlen=MAX_MEMORY_ENTRIES)
        self._total_requests = 0
        self._total_bytes = 0
        self._client_stats: dict[str, dict] = {}  # إحصائيات لكل عميل
        self._load_stats()

    @classmethod
    def get_instance(cls) -> "TrafficLogger":
        """Singleton — نسخة واحدة مشتركة."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log_request(
        self,
        client_ip: str,
        protocol: str,
        target: str,
        method: str = "CONNECT",
        status: str = "success",
        bytes_transferred: int = 0,
    ):
        """تسجيل طلب جديد."""
        now = datetime.now(timezone.utc)

        entry = {
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.isoformat(),
            "client_ip": client_ip,
            "protocol": protocol,
            "method": method,
            "target": target,
            "status": status,
            "bytes": bytes_transferred,
        }

        self._entries.append(entry)
        self._total_requests += 1
        self._total_bytes += bytes_transferred

        # تحديث إحصائيات العميل
        if client_ip not in self._client_stats:
            self._client_stats[client_ip] = {
                "requests": 0,
                "bytes": 0,
                "first_seen": now.isoformat(),
                "last_seen": now.isoformat(),
                "targets": set(),
            }

        cs = self._client_stats[client_ip]
        cs["requests"] += 1
        cs["bytes"] += bytes_transferred
        cs["last_seen"] = now.isoformat()
        cs["targets"].add(target.split(":")[0])  # فقط hostname

        # طباعة في الكونسل
        status_icon = "✓" if status == "success" else "✗"
        logger.info(
            f"[{status_icon}] {client_ip:<18s} → {protocol:<6s} "
            f"{method:<8s} {target}"
        )

    def get_recent(self, count: int = 50) -> list[dict]:
        """آخر N طلبات."""
        entries = list(self._entries)
        return entries[-count:]

    def get_all(self) -> list[dict]:
        """كل الطلبات في الذاكرة."""
        return list(self._entries)

    def get_stats(self) -> dict:
        """إحصائيات عامة."""
        return {
            "total_requests": self._total_requests,
            "total_bytes": self._total_bytes,
            "total_bytes_human": self._human_bytes(self._total_bytes),
            "unique_clients": len(self._client_stats),
            "entries_in_memory": len(self._entries),
        }

    def get_client_stats(self) -> dict:
        """إحصائيات لكل عميل."""
        result = {}
        for ip, stats in self._client_stats.items():
            result[ip] = {
                "requests": stats["requests"],
                "bytes": stats["bytes"],
                "bytes_human": self._human_bytes(stats["bytes"]),
                "first_seen": stats["first_seen"],
                "last_seen": stats["last_seen"],
                "unique_targets": len(stats["targets"]),
                "top_targets": list(stats["targets"])[:10],
            }
        return result

    def get_client_requests(self, client_ip: str, count: int = 50) -> list[dict]:
        """طلبات عميل محدد."""
        return [
            e for e in self._entries
            if e["client_ip"] == client_ip
        ][-count:]

    def clear(self):
        """مسح كل السجلات."""
        self._entries.clear()
        self._total_requests = 0
        self._total_bytes = 0
        self._client_stats.clear()

    def _save_stats(self):
        """حفظ الإحصائيات."""
        try:
            data = {
                "total_requests": self._total_requests,
                "total_bytes": self._total_bytes,
            }
            with open(TRAFFIC_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_stats(self):
        """تحميل الإحصائيات المحفوظة."""
        try:
            if os.path.exists(TRAFFIC_LOG_FILE):
                with open(TRAFFIC_LOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._total_requests = data.get("total_requests", 0)
                self._total_bytes = data.get("total_bytes", 0)
        except Exception:
            pass

    @staticmethod
    def _human_bytes(b: int) -> str:
        """تحويل بايت إلى وحدة مقروءة."""
        for unit in ("B", "KB", "MB", "GB"):
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"
