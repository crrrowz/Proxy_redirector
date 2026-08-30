"""
Proxy Redirector — Online Proxy Fetcher
جلب بروكسيات مجانية من مصادر إنترنت محدّثة تلقائياً.
"""

import asyncio
import logging
import time
from typing import Optional

import aiohttp

import config

logger = logging.getLogger("proxy_fetcher")

# ── المصادر الافتراضية ──
DEFAULT_SOURCES = [
    {
        "url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/refs/heads/main/protocols/https.txt",
        "type": "https",
    },
    {
        "url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/refs/heads/main/protocols/http.txt",
        "type": "http",
    },
    {
        "url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/refs/heads/main/protocols/socks4.txt",
        "type": "socks4",
    },
    {
        "url": "https://raw.githubusercontent.com/iplocate/free-proxy-list/refs/heads/main/protocols/socks5.txt",
        "type": "socks5",
    },
]


class ProxyFetcher:
    """جلب وتحديث بروكسيات من مصادر خارجية بشكل دوري."""

    _instance: Optional["ProxyFetcher"] = None

    def __init__(self):
        self.sources = list(DEFAULT_SOURCES)
        self.enabled = True
        self.paused = False
        self.fetch_interval = getattr(config, "FETCH_INTERVAL_SECONDS", 120)  # كل دقيقتين
        self.last_fetch_time = 0
        self.last_fetch_count = 0
        self.total_fetched = 0
        self.total_added = 0
        self._known_proxies: set[str] = set()  # لمنع التكرار: "ip:port"

    @classmethod
    def get_instance(cls) -> "ProxyFetcher":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def fetch_all(self) -> list[dict]:
        """جلب من كل المصادر وإرجاع قائمة بروكسيات جديدة (غير مكررة)."""
        new_proxies = []

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            for source in self.sources:
                try:
                    proxies = await self._fetch_source(session, source)
                    new_proxies.extend(proxies)
                except Exception as e:
                    logger.warning(f"[FETCH] Failed {source['url']}: {str(e)[:60]}")

        self.last_fetch_time = time.time()
        self.last_fetch_count = len(new_proxies)
        self.total_fetched += len(new_proxies)

        return new_proxies

    async def _fetch_source(self, session: aiohttp.ClientSession, source: dict) -> list[dict]:
        """جلب من مصدر واحد — يتوقع تنسيق ip:port كل سطر."""
        url = source["url"]
        ptype = source.get("type", "socks5")

        async with session.get(url) as response:
            if response.status != 200:
                logger.warning(f"[FETCH] HTTP {response.status} from {url}")
                return []

            text = await response.text()

        proxies = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(":")
            if len(parts) != 2:
                continue

            ip, port_str = parts
            try:
                port = int(port_str)
            except ValueError:
                continue

            key = f"{ip}:{port}"
            if key in self._known_proxies:
                continue  # مكرر

            self._known_proxies.add(key)
            proxies.append({
                "ip": ip.strip(),
                "port": port,
                "type": ptype,
            })

        logger.info(f"[FETCH] {len(proxies)} new from {ptype.upper()} source")
        return proxies

    def add_known(self, ip: str, port: int):
        """تسجيل بروكسي موجود لمنع جلبه مرة ثانية."""
        self._known_proxies.add(f"{ip}:{port}")

    def get_stats(self) -> dict:
        return {
            "enabled": self.enabled,
            "paused": self.paused,
            "last_fetch_time": self.last_fetch_time,
            "last_fetch_count": self.last_fetch_count,
            "total_fetched": self.total_fetched,
            "total_added": self.total_added,
            "known_count": len(self._known_proxies),
            "sources_count": len(self.sources),
            "interval_seconds": self.fetch_interval,
        }
