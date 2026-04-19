"""
Proxy Redirector — Ad Block Manager
محرك حظر الإعلانات والمحتوى غير المرغوب فيه

الميزات:
  - حظر الدومينات بالضبط (O(1) via set)
  - حظر بأنماط عامة (wildcard) مثل *ads* أو *.doubleclick.net
  - قائمة بيضاء (استثناءات) تتجاوز الحظر
  - تصنيفات مستقلة (إعلانات، تتبع، برمجيات خبيثة، مخصص) مع تشغيل/إيقاف لكل فئة
  - إحصائيات حظر مفصلة
  - قائمة سوداء افتراضية لأشهر دومينات الإعلانات والتتبع
"""

import json
import os
import logging
from fnmatch import fnmatch
from typing import Optional
from collections import defaultdict

import config

logger = logging.getLogger("adblock")

# ── مسار ملف القواعد ──
_BLOCKLIST_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    getattr(config, "BLOCKLIST_FILE", "data/blocklist.json"),
)

# ── التصنيفات المدعومة ──
CATEGORIES = ["ads", "tracking", "malware", "custom"]

# ── قائمة سوداء افتراضية ──
DEFAULT_RULES = [
    # ── إعلانات (ads) ──
    {"domain": "doubleclick.net", "category": "ads"},
    {"domain": "googlesyndication.com", "category": "ads"},
    {"domain": "googleadservices.com", "category": "ads"},
    {"domain": "google-analytics.com", "category": "ads"},
    {"domain": "adnxs.com", "category": "ads"},
    {"domain": "adsrvr.org", "category": "ads"},
    {"domain": "adcolony.com", "category": "ads"},
    {"domain": "admob.com", "category": "ads"},
    {"domain": "moatads.com", "category": "ads"},
    {"domain": "serving-sys.com", "category": "ads"},
    {"domain": "advertising.com", "category": "ads"},
    {"domain": "pubmatic.com", "category": "ads"},
    {"domain": "openx.net", "category": "ads"},
    {"domain": "rubiconproject.com", "category": "ads"},
    {"domain": "smartadserver.com", "category": "ads"},
    {"domain": "taboola.com", "category": "ads"},
    {"domain": "outbrain.com", "category": "ads"},
    {"domain": "criteo.com", "category": "ads"},
    {"domain": "criteo.net", "category": "ads"},
    {"domain": "unity3d.com", "category": "ads"},
    {"domain": "applovin.com", "category": "ads"},
    {"domain": "mopub.com", "category": "ads"},
    {"domain": "inmobi.com", "category": "ads"},
    {"domain": "smaato.net", "category": "ads"},
    {"domain": "chartboost.com", "category": "ads"},

    # ── تتبع (tracking) ──
    {"domain": "facebook.net", "category": "tracking"},
    {"domain": "connect.facebook.net", "category": "tracking"},
    {"domain": "pixel.facebook.com", "category": "tracking"},
    {"domain": "analytics.google.com", "category": "tracking"},
    {"domain": "hotjar.com", "category": "tracking"},
    {"domain": "mixpanel.com", "category": "tracking"},
    {"domain": "amplitude.com", "category": "tracking"},
    {"domain": "segment.com", "category": "tracking"},
    {"domain": "segment.io", "category": "tracking"},
    {"domain": "branch.io", "category": "tracking"},
    {"domain": "adjust.com", "category": "tracking"},
    {"domain": "appsflyer.com", "category": "tracking"},
    {"domain": "kochava.com", "category": "tracking"},
    {"domain": "scorecardresearch.com", "category": "tracking"},
    {"domain": "quantserve.com", "category": "tracking"},
    {"domain": "newrelic.com", "category": "tracking"},
    {"domain": "crazyegg.com", "category": "tracking"},
    {"domain": "mouseflow.com", "category": "tracking"},
    {"domain": "fullstory.com", "category": "tracking"},
    {"domain": "clarity.ms", "category": "tracking"},

    # ── برمجيات خبيثة (malware) ──
    {"domain": "malware-check.disconnect.me", "category": "malware"},
    {"domain": "malwaredomainlist.com", "category": "malware"},
]

# ── أنماط wildcard افتراضية ──
DEFAULT_WILDCARD_RULES = [
    {"pattern": "*ads.*", "category": "ads"},
    {"pattern": "*tracker.*", "category": "tracking"},
    {"pattern": "*tracking.*", "category": "tracking"},
    {"pattern": "*adserver*", "category": "ads"},
    {"pattern": "*banner*ad*", "category": "ads"},
]


class AdBlockManager:
    """
    محرك حظر الإعلانات — Singleton.
    يعمل كفلتر يتم استدعاؤه عند كل طلب اتصال.
    """

    _instance: Optional["AdBlockManager"] = None

    def __init__(self):
        # القواعد
        self._exact_domains: dict[str, str] = {}      # domain -> category
        self._wildcard_rules: list[dict] = []          # [{pattern, category}]
        self._whitelist: set[str] = set()              # استثناءات

        # حالة التصنيفات (مفعّلة/معطّلة)
        self._categories_enabled: dict[str, bool] = {
            cat: True for cat in CATEGORIES
        }

        # الحالة العامة
        self._enabled: bool = getattr(config, "ADBLOCK_ENABLED", True)

        # إحصائيات
        self._total_blocked: int = 0
        self._blocked_per_domain: defaultdict = defaultdict(int)
        self._blocked_per_category: defaultdict = defaultdict(int)

        # تحميل القواعد
        self._load()

    @classmethod
    def get_instance(cls) -> "AdBlockManager":
        """Singleton — نسخة واحدة مشتركة."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ══════════════════════════════════════════════
    # الفحص الرئيسي — يُستدعى عند كل طلب
    # ══════════════════════════════════════════════

    def is_blocked(self, host: str, path: str = "") -> bool:
        """
        هل هذا الهدف محظور؟
        يتحقق من الدومين والمسار.
        يعيد True إذا كان محظوراً و False إذا كان مسموحاً.
        """
        if not self._enabled:
            return False

        if not host:
            return False

        host_lower = host.lower().strip()

        # 1. القائمة البيضاء تتجاوز كل شيء
        if host_lower in self._whitelist:
            return False

        # تحقق من الدومينات الفرعية في القائمة البيضاء
        parts = host_lower.split(".")
        for i in range(len(parts)):
            parent = ".".join(parts[i:])
            if parent in self._whitelist:
                return False

        # 2. فحص الدومين بالضبط (O(1))
        # تحقق من الدومين نفسه + كل الدومينات الأب
        for i in range(len(parts)):
            check_domain = ".".join(parts[i:])
            if check_domain in self._exact_domains:
                category = self._exact_domains[check_domain]
                if self._categories_enabled.get(category, True):
                    self._record_block(host_lower, category)
                    return True

        # 3. فحص الأنماط العامة (wildcard)
        full_target = host_lower + path.lower()
        for rule in self._wildcard_rules:
            category = rule["category"]
            if not self._categories_enabled.get(category, True):
                continue
            if fnmatch(host_lower, rule["pattern"]) or fnmatch(full_target, rule["pattern"]):
                self._record_block(host_lower, category)
                return True

        return False

    def _record_block(self, domain: str, category: str):
        """تسجيل إحصائية الحظر."""
        self._total_blocked += 1
        self._blocked_per_domain[domain] += 1
        self._blocked_per_category[category] += 1

    # ══════════════════════════════════════════════
    # إدارة القواعد
    # ══════════════════════════════════════════════

    def add_rule(self, domain: str, category: str = "custom") -> bool:
        """إضافة قاعدة حظر جديدة."""
        domain = domain.lower().strip()
        if not domain:
            return False

        category = category.lower() if category else "custom"
        if category not in CATEGORIES:
            category = "custom"

        # هل هو نمط wildcard؟
        if "*" in domain or "?" in domain:
            # تأكد أنه غير موجود
            for rule in self._wildcard_rules:
                if rule["pattern"] == domain:
                    return False
            self._wildcard_rules.append({"pattern": domain, "category": category})
        else:
            self._exact_domains[domain] = category

        self._save()
        logger.info(f"[ADBLOCK] Rule added: {domain} ({category})")
        return True

    def remove_rule(self, domain: str) -> bool:
        """إزالة قاعدة حظر."""
        domain = domain.lower().strip()

        # حاول إزالته من الدومينات
        if domain in self._exact_domains:
            del self._exact_domains[domain]
            self._save()
            logger.info(f"[ADBLOCK] Rule removed: {domain}")
            return True

        # حاول إزالته من الأنماط
        for i, rule in enumerate(self._wildcard_rules):
            if rule["pattern"] == domain:
                self._wildcard_rules.pop(i)
                self._save()
                logger.info(f"[ADBLOCK] Wildcard rule removed: {domain}")
                return True

        return False

    def add_whitelist(self, domain: str) -> bool:
        """إضافة دومين إلى القائمة البيضاء (استثناء)."""
        domain = domain.lower().strip()
        if not domain:
            return False
        self._whitelist.add(domain)
        self._save()
        logger.info(f"[ADBLOCK] Whitelist added: {domain}")
        return True

    def remove_whitelist(self, domain: str) -> bool:
        """إزالة دومين من القائمة البيضاء."""
        domain = domain.lower().strip()
        if domain in self._whitelist:
            self._whitelist.discard(domain)
            self._save()
            logger.info(f"[ADBLOCK] Whitelist removed: {domain}")
            return True
        return False

    # ══════════════════════════════════════════════
    # التصنيفات
    # ══════════════════════════════════════════════

    def toggle_category(self, category: str, enabled: bool):
        """تشغيل/إيقاف تصنيف محدد."""
        category = category.lower()
        if category in self._categories_enabled:
            self._categories_enabled[category] = enabled
            self._save()
            state = "ON" if enabled else "OFF"
            logger.info(f"[ADBLOCK] Category '{category}' → {state}")

    def toggle_enabled(self, enabled: bool):
        """تشغيل/إيقاف المحرك بالكامل."""
        self._enabled = enabled
        self._save()
        state = "ON" if enabled else "OFF"
        logger.info(f"[ADBLOCK] Engine → {state}")

    # ══════════════════════════════════════════════
    # البيانات (للـ API والـ GUI)
    # ══════════════════════════════════════════════

    @property
    def enabled(self) -> bool:
        return self._enabled

    def get_rules(self) -> list[dict]:
        """كل القواعد كقائمة."""
        rules = []
        for domain, category in self._exact_domains.items():
            rules.append({"domain": domain, "category": category, "type": "exact"})
        for rule in self._wildcard_rules:
            rules.append({"domain": rule["pattern"], "category": rule["category"], "type": "wildcard"})
        return rules

    def get_whitelist(self) -> list[str]:
        """قائمة الاستثناءات."""
        return sorted(self._whitelist)

    def get_categories(self) -> dict[str, bool]:
        """حالة التصنيفات."""
        return dict(self._categories_enabled)

    def get_stats(self) -> dict:
        """إحصائيات الحظر."""
        # أعلى 10 دومينات محظورة
        top_domains = sorted(
            self._blocked_per_domain.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "enabled": self._enabled,
            "total_blocked": self._total_blocked,
            "total_rules": len(self._exact_domains) + len(self._wildcard_rules),
            "total_whitelist": len(self._whitelist),
            "blocked_per_category": dict(self._blocked_per_category),
            "top_blocked_domains": [
                {"domain": d, "count": c} for d, c in top_domains
            ],
        }

    # ══════════════════════════════════════════════
    # التحميل والحفظ
    # ══════════════════════════════════════════════

    def _save(self):
        """حفظ القواعد إلى ملف."""
        try:
            data = {
                "enabled": self._enabled,
                "categories_enabled": self._categories_enabled,
                "exact_domains": self._exact_domains,
                "wildcard_rules": self._wildcard_rules,
                "whitelist": list(self._whitelist),
            }
            with open(_BLOCKLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[ADBLOCK] Failed to save blocklist: {e}")

    def _load(self):
        """تحميل القواعد من الملف أو إنشاء القائمة الافتراضية."""
        if os.path.exists(_BLOCKLIST_FILE):
            try:
                with open(_BLOCKLIST_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._enabled = data.get("enabled", True)
                self._categories_enabled = data.get(
                    "categories_enabled",
                    {cat: True for cat in CATEGORIES},
                )
                self._exact_domains = data.get("exact_domains", {})
                self._wildcard_rules = data.get("wildcard_rules", [])
                self._whitelist = set(data.get("whitelist", []))

                total = len(self._exact_domains) + len(self._wildcard_rules)
                logger.info(
                    f"[ADBLOCK] Loaded {total} rules, "
                    f"{len(self._whitelist)} whitelist entries"
                )
                return
            except Exception as e:
                logger.error(f"[ADBLOCK] Failed to load blocklist: {e}")

        # لا يوجد ملف → إنشاء القائمة الافتراضية
        logger.info("[ADBLOCK] Creating default blocklist...")
        for rule in DEFAULT_RULES:
            self._exact_domains[rule["domain"]] = rule["category"]
        for rule in DEFAULT_WILDCARD_RULES:
            self._wildcard_rules.append(rule)

        self._save()
        total = len(self._exact_domains) + len(self._wildcard_rules)
        logger.info(f"[ADBLOCK] Created default blocklist with {total} rules")

    def reload(self):
        """إعادة تحميل القواعد من الملف."""
        self._exact_domains.clear()
        self._wildcard_rules.clear()
        self._whitelist.clear()
        self._load()
