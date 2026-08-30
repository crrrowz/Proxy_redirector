"""
Proxy Redirector — Failover Handler v2
التبديل الهادئ: لا يقتل البروكسيات — فقط يقترح التبديل.
الـ checker هو الوحيد الذي يحدد الحالة.
"""

import asyncio
import logging
import time
from typing import Optional

from core.proxy_manager import ProxyManager
import config

logger = logging.getLogger("failover")


class FailoverHandler:
    def __init__(self, manager: ProxyManager):
        self.manager = manager
        self._current_proxy: Optional[dict] = None
        self._lock = asyncio.Lock()
        self._switch_count = 0
        self._last_switch_time: Optional[float] = None

    @property
    def current_proxy(self) -> Optional[dict]:
        return self._current_proxy

    @property
    def switch_count(self) -> int:
        return self._switch_count

    async def initialize(self):
        """اختيار أفضل بروكسي (يفضّل SSL-verified) كبداية."""
        async with self._lock:
            best = self.manager.get_fastest_proxy()
            if best:
                self._current_proxy = best
                st = self.manager.get_proxy_status(best["id"])
                ssl_tag = " [SSL ✓]" if st.get("ssl_verified", False) else ""
                logger.info(
                    f"[INIT] Active proxy: {best['id']} "
                    f"({best['ip']}:{best['port']} {best['type']}){ssl_tag}"
                )
            else:
                logger.warning("[INIT] No working proxy available yet")
                self._current_proxy = None

    async def get_active_proxy(self) -> Optional[dict]:
        """إرجاع البروكسي النشط."""
        async with self._lock:
            if self._current_proxy is None:
                best = self.manager.get_fastest_proxy()
                if best:
                    self._current_proxy = best
            return self._current_proxy

    async def suggest_switch(self, better_proxy: dict):
        """
        اقتراح التبديل: عندما ينجح بروكسي آخر في الاتصال
        بينما النشط فشل. لا يقتل أحداً.
        """
        async with self._lock:
            if getattr(self, '_manual_lock', False):
                return  # الاختيار اليدوي مقفل — لا تغيّر
            if (
                self._current_proxy is None
                or better_proxy["id"] != self._current_proxy["id"]
            ):
                old_id = self._current_proxy["id"] if self._current_proxy else "None"
                self._current_proxy = better_proxy
                self._switch_count += 1
                self._last_switch_time = time.time()
                logger.info(
                    f"[SWITCH] {old_id} -> {better_proxy['id']} "
                    f"({better_proxy['ip']}:{better_proxy['port']})"
                )

    async def refresh_best(self):
        """
        إعادة اختيار الأسرع بعد جولة فحص.
        يُستدعى من الـ checker فقط.
        """
        async with self._lock:
            if getattr(self, '_manual_lock', False):
                return  # الاختيار اليدوي مقفل
            best = self.manager.get_fastest_proxy()
            if best is None:
                if self._current_proxy is not None:
                    logger.warning("[REFRESH] No alive proxy after check!")
                    self._current_proxy = None
                return

            if (
                self._current_proxy is None
                or best["id"] != self._current_proxy["id"]
            ):
                old_id = self._current_proxy["id"] if self._current_proxy else "None"
                self._current_proxy = best
                self._switch_count += 1
                self._last_switch_time = time.time()
                logger.info(
                    f"[REFRESH] {old_id} -> {best['id']} "
                    f"({best['ip']}:{best['port']})"
                )

    async def force_select(self, proxy: dict):
        """اختيار يدوي لبروكسي معيّن — يقفل الاختيار التلقائي."""
        async with self._lock:
            old_id = self._current_proxy["id"] if self._current_proxy else "None"
            self._current_proxy = proxy
            self._manual_lock = True
            self._switch_count += 1
            self._last_switch_time = time.time()
            logger.info(
                f"[MANUAL] Forced: {old_id} -> {proxy['id']} "
                f"({proxy['ip']}:{proxy['port']}) — auto-switch disabled"
            )

    def unlock_auto(self):
        """إعادة تفعيل الاختيار التلقائي."""
        self._manual_lock = False
        logger.info("[MANUAL] Auto-switch re-enabled")

    @property
    def is_manual_locked(self) -> bool:
        return getattr(self, '_manual_lock', False)

    def get_status_summary(self) -> dict:
        return {
            "current_proxy": self._current_proxy,
            "switch_count": self._switch_count,
            "last_switch": self._last_switch_time,
            "manual_locked": self.is_manual_locked,
        }
