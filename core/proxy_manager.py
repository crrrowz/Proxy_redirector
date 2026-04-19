"""
Proxy Redirector — Proxy Manager
إدارة البروكسيات مع نظام الفرصة الثانية:
 - البروكسي الذي تعطل مؤقتاً يُعاد فحصه بعد 5 دقائق
 - لا يُستبعد نهائياً إلا بعد 15 فشل متتالي
 - البروكسيات الميتة تُعاد فحصها دورياً (الأقل فشلاً أولاً)
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional

import config

logger = logging.getLogger("proxy_manager")


def _normalize_proxy(raw: dict, index: int) -> dict:
    """تحويل بروكسي من أي تنسيق إلى التنسيق الموحّد."""
    ptype = raw.get("type") or raw.get("protocol") or "socks5"
    ptype = ptype.lower()
    if ptype == "http":
        ptype = "https"

    geo = raw.get("geolocation", {})
    return {
        "id": raw.get("id", f"proxy_{index:05d}"),
        "ip": raw["ip"],
        "port": int(raw["port"]),
        "type": ptype,
        "username": raw.get("username"),
        "password": raw.get("password"),
        "country": geo.get("country", "??"),
        "city": geo.get("city", "Unknown"),
    }


class ProxyManager:
    """مدير البروكسيات مع نظام الفرصة الثانية."""

    def __init__(self):
        self.proxies: list[dict] = []
        self._all_proxies: list[dict] = []  # unfiltered
        self._proxies_by_id: dict[str, dict] = {}
        self.status: dict[str, dict] = {}
        self._sorted_proxies: list[dict] = []

    def load_proxies(self) -> list[dict]:
        """تحميل البروكسيات من ملف JSON."""
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            config.PROXIES_FILE,
        )
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                raw_list = data
            elif isinstance(data, dict) and "proxies" in data:
                raw_list = data["proxies"]
            else:
                logger.error("[ERROR] Unknown JSON format!")
                self.proxies = []
                return self.proxies

            self._all_proxies = []
            for i, raw in enumerate(raw_list):
                try:
                    normalized = _normalize_proxy(raw, i)
                    self._all_proxies.append(normalized)
                except (KeyError, ValueError) as e:
                    pass  # تخطي البروكسيات غير الصالحة بصمت

            # فلترة حسب البلد
            country_filter = getattr(config, "COUNTRY_FILTER", "GLOBAL").upper()
            if country_filter and country_filter != "GLOBAL":
                self.proxies = [
                    p for p in self._all_proxies
                    if p["country"].upper() == country_filter
                ]
                logger.info(
                    f"[FILTER] Country={country_filter}: "
                    f"{len(self.proxies)}/{len(self._all_proxies)} proxies"
                )
            else:
                self.proxies = list(self._all_proxies)

            # بناء فهرس سريع
            self._proxies_by_id = {p["id"]: p for p in self.proxies}

            logger.info(
                f"[LOAD] {len(self.proxies)} proxies from {config.PROXIES_FILE}"
            )

        except FileNotFoundError:
            logger.error(f"[ERROR] File {config.PROXIES_FILE} not found!")
            self.proxies = []
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] JSON parse error: {e}")
            self.proxies = []

        self._load_status()
        return self.proxies

    def _load_status(self):
        """تحميل حالة البروكسيات المحفوظة."""
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            config.STATUS_FILE,
        )
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.status = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.status = {}
        else:
            self.status = {}

    def _save_status(self):
        """حفظ حالة البروكسيات."""
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            config.STATUS_FILE,
        )
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.status, f, indent=2, ensure_ascii=False, default=str)
        except IOError as e:
            logger.error(f"[ERROR] Can't save status: {e}")

    def update_status(self, check_results: list[dict]):
        """تحديث حالة البروكسيات بناءً على نتائج الفحص."""
        now = datetime.now(timezone.utc).isoformat()

        for result in check_results:
            proxy_id = result["id"]

            if proxy_id not in self.status:
                self.status[proxy_id] = {
                    "alive": False,
                    "last_checked": None,
                    "response_time_ms": None,
                    "consecutive_failures": 0,
                    "last_success": None,
                    "total_checks": 0,
                    "total_successes": 0,
                }

            entry = self.status[proxy_id]
            entry["last_checked"] = now
            entry["total_checks"] += 1

            if result["alive"]:
                entry["alive"] = True
                entry["response_time_ms"] = result["response_time_ms"]
                entry["consecutive_failures"] = 0  # ← يُصفّر الفشل عند النجاح
                entry["last_success"] = now
                entry["total_successes"] += 1
            else:
                entry["alive"] = False
                entry["response_time_ms"] = None
                entry["consecutive_failures"] += 1

        self._save_status()
        self._sort_proxies()

    # ──────────────────────────────────────────
    # نظام الفرصة الثانية
    # ──────────────────────────────────────────

    def get_dead_proxies_for_retry(self) -> list[dict]:
        """
        إرجاع البروكسيات الميتة المؤهلة لإعادة الفحص:
        - مرّ عليها وقت كافٍ (DEAD_RETRY_AFTER_SECONDS)
        - لم تتجاوز حد الاستبعاد النهائي (BLACKLIST_AFTER_FAILURES)
        - مرتبة: الأقل فشلاً أولاً (الأكثر أملاً في العودة)
        """
        now = datetime.now(timezone.utc)
        candidates = []

        for proxy_id, st in self.status.items():
            # تخطي العاملين
            if st.get("alive", False):
                continue

            # تخطي المُستبعدين نهائياً
            fails = st.get("consecutive_failures", 0)
            if fails >= config.BLACKLIST_AFTER_FAILURES:
                continue

            # تحقق من مرور وقت كافٍ
            last_checked = st.get("last_checked")
            if last_checked:
                try:
                    checked_at = datetime.fromisoformat(last_checked)
                    age_seconds = (now - checked_at).total_seconds()
                    if age_seconds < config.DEAD_RETRY_AFTER_SECONDS:
                        continue  # ← لم يمرّ وقت كافٍ
                except (ValueError, TypeError):
                    pass

            # مؤهل لإعادة الفحص
            proxy = self._proxies_by_id.get(proxy_id)
            if proxy:
                candidates.append((fails, proxy))

        # ترتيب: الأقل فشلاً أولاً (أكثر أمل في العودة)
        candidates.sort(key=lambda x: x[0])

        # إرجاع الدفعة المطلوبة فقط
        return [c[1] for c in candidates[: config.DEAD_RECHECK_BATCH]]

    def get_unchecked_proxies(self, count: int) -> list[dict]:
        """إرجاع بروكسيات لم تُفحص أبداً."""
        unchecked = [
            p for p in self.proxies
            if p["id"] not in self.status
        ]
        import random
        random.shuffle(unchecked)
        return unchecked[:count]

    def is_blacklisted(self, proxy_id: str) -> bool:
        """هل البروكسي مُستبعد نهائياً؟"""
        st = self.status.get(proxy_id, {})
        return st.get("consecutive_failures", 0) >= config.BLACKLIST_AFTER_FAILURES

    # ──────────────────────────────────────────
    # الترتيب
    # ──────────────────────────────────────────

    def _calculate_score(self, proxy_id: str) -> float:
        """حساب نقاط البروكسي للترتيب."""
        if proxy_id not in self.status:
            return 0.0

        s = self.status[proxy_id]
        score = 0.0

        # حي = 50 نقطة
        if s["alive"]:
            score += config.SCORE_ALIVE

        # السرعة: 0-25
        if s["response_time_ms"] is not None and s["response_time_ms"] > 0:
            speed_ratio = max(0, 1 - (s["response_time_ms"] / config.SPEED_THRESHOLD_MS))
            score += speed_ratio * config.SCORE_SPEED_MAX

        # حداثة: 0-15
        if s["last_success"]:
            try:
                last_ok = datetime.fromisoformat(s["last_success"])
                age_minutes = (datetime.now(timezone.utc) - last_ok).total_seconds() / 60
                recency = max(0, 1 - (age_minutes / 60))
                score += recency * config.SCORE_RECENCY_MAX
            except (ValueError, TypeError):
                pass

        # خصم فشل متتالي
        score -= s["consecutive_failures"] * config.SCORE_FAILURE_PENALTY

        # نسبة النجاح: 0-10
        if s["total_checks"] > 0:
            rate = s["total_successes"] / s["total_checks"]
            score += rate * config.SCORE_SUCCESS_RATE_MAX

        return score

    def _sort_proxies(self):
        """ترتيب البروكسيات حسب النقاط."""
        scored = []
        for proxy in self.proxies:
            pid = proxy["id"]
            if pid in self.status:
                sc = self._calculate_score(pid)
                scored.append((sc, proxy))

        scored.sort(key=lambda x: x[0], reverse=True)
        self._sorted_proxies = [item[1] for item in scored]

    def get_sorted_proxies(self) -> list[dict]:
        if not self._sorted_proxies:
            self._sort_proxies()
        return self._sorted_proxies

    def get_alive_proxies(self) -> list[dict]:
        return [
            p for p in self.get_sorted_proxies()
            if self.status.get(p["id"], {}).get("alive", False)
        ]

    def get_best_proxy(self) -> Optional[dict]:
        alive = self.get_alive_proxies()
        return alive[0] if alive else None

    def get_fastest_proxy(self) -> Optional[dict]:
        """إرجاع أسرع بروكسي من حيث الاستجابة (ping)."""
        alive = self.get_alive_proxies()
        if not alive:
            return None
        
        # ترتيب حسب السرعة (الأقل هو الأفضل)
        def get_speed(p):
            return self.status.get(p["id"], {}).get("response_time_ms") or 9999.0
            
        alive.sort(key=get_speed)
        return alive[0]

    def get_next_proxy(self, current_id: str) -> Optional[dict]:
        alive = self.get_alive_proxies()
        if not alive:
            return None
        for i, p in enumerate(alive):
            if p["id"] == current_id:
                next_idx = (i + 1) % len(alive)
                return alive[next_idx]
        return alive[0]

    def mark_proxy_dead(self, proxy_id: str):
        """تعليم بروكسي كميت عند الفشل الفعلي."""
        if proxy_id in self.status:
            self.status[proxy_id]["alive"] = False
            self.status[proxy_id]["consecutive_failures"] += 1
            fails = self.status[proxy_id]["consecutive_failures"]
            self._save_status()
            self._sort_proxies()

            if fails < config.MAX_CONSECUTIVE_FAILURES:
                logger.warning(
                    f"[FAIL] {proxy_id} failed ({fails}/{config.MAX_CONSECUTIVE_FAILURES}) "
                    f"-- will retry later"
                )
            elif fails < config.BLACKLIST_AFTER_FAILURES:
                logger.warning(
                    f"[DEAD] {proxy_id} failed {fails}x -- retry in "
                    f"{config.DEAD_RETRY_AFTER_SECONDS}s"
                )
            else:
                logger.error(
                    f"[BLACKLIST] {proxy_id} failed {fails}x -- permanently excluded"
                )

    def get_proxy_status(self, proxy_id: str) -> dict:
        return self.status.get(proxy_id, {})

    def get_dashboard_data(self) -> list[dict]:
        result = []
        for proxy in self.get_sorted_proxies():
            pid = proxy["id"]
            st = self.status.get(pid, {})
            score = self._calculate_score(pid)
            result.append({"proxy": proxy, "status": st, "score": score})
        return result

    def get_pool_summary(self) -> dict:
        """ملخص حالة المجموعة."""
        alive = 0
        dead_retryable = 0
        blacklisted = 0
        unchecked = 0

        checked_ids = set(self.status.keys())

        for proxy in self.proxies:
            pid = proxy["id"]
            if pid not in checked_ids:
                unchecked += 1
            elif self.status[pid].get("alive", False):
                alive += 1
            elif self.status[pid].get("consecutive_failures", 0) >= config.BLACKLIST_AFTER_FAILURES:
                blacklisted += 1
            else:
                dead_retryable += 1

        return {
            "alive": alive,
            "dead_retryable": dead_retryable,
            "blacklisted": blacklisted,
            "unchecked": unchecked,
            "total": len(self.proxies),
        }

    def get_available_countries(self) -> list[dict]:
        """إرجاع قائمة البلدان المتاحة مع عدد البروكسيات."""
        from collections import Counter
        source = self._all_proxies if self._all_proxies else self.proxies
        counts = Counter(p["country"] for p in source)
        result = [{"code": code, "count": count} for code, count in counts.items()]
        result.sort(key=lambda x: x["count"], reverse=True)
        return result
