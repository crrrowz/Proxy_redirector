"""
Proxy Redirector — Proxy Checker
فحص البروكسيات بالدفعات: يبحث حتى يجد العدد المطلوب فقط
مع فحص الهوية (Anonymity Check): يتأكد أن البروكسي يخفي IP الحقيقي
"""

import asyncio
import time
import logging
import random
from typing import Optional

import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType

import config

logger = logging.getLogger("proxy_checker")


async def detect_real_ip() -> Optional[str]:
    """
    اكتشاف IP الحقيقي للمستخدم (بدون بروكسي).
    يُستخدم عدة خدمات للتأكد.
    """
    services = [
        "http://httpbin.org/ip",
        "http://api.ipify.org?format=json",
        "http://ifconfig.me/ip",
    ]

    timeout = aiohttp.ClientTimeout(total=10)

    for url in services:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        # httpbin returns {"origin": "x.x.x.x"}
                        if "origin" in text:
                            import json
                            data = json.loads(text)
                            ip = data["origin"].split(",")[0].strip()
                        elif "ip" in text and "{" in text:
                            import json
                            data = json.loads(text)
                            ip = data["ip"].strip()
                        else:
                            ip = text.strip()

                        logger.info(f"[REAL IP] Detected: {ip}")
                        return ip
        except Exception:
            continue

    logger.error("[REAL IP] Could not detect real IP!")
    return None


def _get_proxy_type(type_str: str) -> ProxyType:
    """تحويل نص نوع البروكسي إلى ProxyType enum."""
    mapping = {
        "socks5": ProxyType.SOCKS5,
        "socks4": ProxyType.SOCKS4,
        "https": ProxyType.HTTP,
        "http": ProxyType.HTTP,
    }
    return mapping.get(type_str.lower(), ProxyType.SOCKS5)


def _build_proxy_url(proxy: dict) -> str:
    """بناء URL البروكسي من بياناته."""
    ptype = proxy["type"].lower()
    scheme_map = {
        "socks5": "socks5",
        "socks4": "socks4",
        "https": "http",
        "http": "http",
    }
    scheme = scheme_map.get(ptype, "socks5")

    auth = ""
    if proxy.get("username") and proxy.get("password"):
        auth = f"{proxy['username']}:{proxy['password']}@"

    return f"{scheme}://{auth}{proxy['ip']}:{proxy['port']}"


async def check_single_proxy(proxy: dict) -> dict:
    """
    فحص بروكسي واحد:
    1. هل يعمل؟
    2. هل يخفي IP الحقيقي؟ (Anonymity Check)
    يعيد dict بالنتيجة.
    """
    proxy_id = proxy["id"]
    proxy_url = _build_proxy_url(proxy)
    result = {
        "id": proxy_id,
        "alive": False,
        "response_time_ms": None,
        "error": None,
    }

    try:
        connector = ProxyConnector.from_url(proxy_url, rdns=True)  # ← DNS عن بُعد
        timeout = aiohttp.ClientTimeout(total=config.CHECK_TIMEOUT_SECONDS)

        start = time.monotonic()
        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            async with session.get(config.CHECK_URL) as response:
                elapsed = (time.monotonic() - start) * 1000  # ms
                if response.status == 200:
                    # ═══ فحص الهوية: هل البروكسي يخفي IP الحقيقي؟ ═══
                    if config.ANONYMITY_CHECK and config.REAL_IP:
                        try:
                            import json as _json
                            body = await response.text()
                            data = _json.loads(body)
                            returned_ip = data.get("origin", "").split(",")[0].strip()

                            if returned_ip == config.REAL_IP:
                                # بروكسي شفاف — يكشف IP الحقيقي!
                                result["error"] = "TRANSPARENT — leaks real IP!"
                                logger.warning(
                                    f"[LEAK] {proxy_id} ({proxy['ip']}:{proxy['port']}) "
                                    f"— returned real IP {returned_ip}! REJECTED"
                                )
                                return result
                        except Exception:
                            pass  # إذا فشل التحليل، اعتبره ناجحاً

                    result["alive"] = True
                    result["response_time_ms"] = round(elapsed, 1)

                    # ═══ Speed threshold check ═══
                    max_speed = getattr(config, "MAX_SPEED_MS", 0)
                    if max_speed > 0 and elapsed > max_speed:
                        result["alive"] = False
                        result["error"] = f"Too slow ({elapsed:.0f}ms > {max_speed}ms)"
                        return result

                    logger.info(
                        f"[OK] {proxy_id} ({proxy['ip']}:{proxy['port']}) "
                        f"-- {elapsed:.0f}ms"
                    )
                else:
                    result["error"] = f"HTTP {response.status}"
    except asyncio.TimeoutError:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:80]

    return result


async def check_batch(proxies: list[dict]) -> list[dict]:
    """فحص دفعة واحدة من البروكسيات بشكل متزامن."""
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_CHECKS)

    async def _limited(proxy: dict) -> dict:
        async with semaphore:
            return await check_single_proxy(proxy)

    tasks = [_limited(p) for p in proxies]
    results = await asyncio.gather(*tasks)

    # ═══ تسجيل النتائج في التحليلات ═══
    try:
        from core.proxy_analytics import ProxyAnalytics
        analytics = ProxyAnalytics.get_instance()
        proxy_map = {p["id"]: p for p in proxies}
        for r in results:
            proxy = proxy_map.get(r["id"])
            country = proxy.get("country", "??") if proxy else "??"
            analytics.record_check(r["id"], r["alive"], r.get("response_time_ms"), country)
    except Exception:
        pass  # لا نوقف الفحص بسبب خطأ في التحليلات

    return results


async def find_alive_proxies(
    all_proxies: list[dict],
    needed: int,
    already_checked_ids: set[str] | None = None,
) -> list[dict]:
    """
    البحث عن بروكسيات تعمل بالدفعات.
    يتوقف فوراً عند إيجاد العدد المطلوب (needed).
    
    Args:
        all_proxies: جميع البروكسيات من الملف
        needed: عدد البروكسيات المطلوبة
        already_checked_ids: IDs سبق فحصها (لتجنب التكرار)
    
    Returns:
        قائمة نتائج الفحص (جميعها، ليس فقط الناجحة)
    """
    if already_checked_ids is None:
        already_checked_ids = set()

    # فلترة البروكسيات التي لم تُفحص بعد
    unchecked = [
        p for p in all_proxies if p["id"] not in already_checked_ids
    ]

    # خلط عشوائي لتنويع البروكسيات
    random.shuffle(unchecked)

    all_results = []
    alive_found = 0
    batch_num = 0

    for start in range(0, len(unchecked), config.BATCH_SIZE):
        if alive_found >= needed:
            break

        batch_num += 1
        batch = unchecked[start : start + config.BATCH_SIZE]

        logger.info(
            f"[BATCH {batch_num}] Checking {len(batch)} proxies... "
            f"(found {alive_found}/{needed} so far)"
        )

        results = await check_batch(batch)
        all_results.extend(results)

        # عدّ الناجحين
        alive_found += sum(1 for r in results if r["alive"])

        if alive_found >= needed:
            logger.info(
                f"[DONE] Found {alive_found} working proxies! "
                f"(checked {len(all_results)} total)"
            )

    if alive_found < needed:
        logger.warning(
            f"[WARN] Only found {alive_found}/{needed} working proxies "
            f"after checking {len(all_results)}"
        )

    return all_results


async def recheck_alive_proxies(alive_proxies: list[dict]) -> list[dict]:
    """
    إعادة فحص البروكسيات العاملة فقط (للتأكد أنها ما زالت تعمل).
    """
    if not alive_proxies:
        return []

    logger.info(
        f"[RECHECK] Verifying {len(alive_proxies)} working proxies..."
    )
    results = await check_batch(alive_proxies)

    still_alive = sum(1 for r in results if r["alive"])
    logger.info(
        f"[RECHECK] {still_alive}/{len(alive_proxies)} still working"
    )

    return results
