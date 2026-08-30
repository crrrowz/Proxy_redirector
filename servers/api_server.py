"""
Proxy Redirector — API Server
سيرفر HTTP API داخلي يربط واجهة GUI بمحرك البروكسي.
يعمل على 127.0.0.1:9090 ويقدم:
  - REST API للبيانات الحية
  - ملفات static للواجهة
"""

import asyncio
import json
import os
import sys
import socket
import logging
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote

import config
from core.proxy_manager import ProxyManager
from core.proxy_checker import find_alive_proxies, recheck_alive_proxies, check_batch, detect_real_ip
from core.failover_handler import FailoverHandler
from servers.socks5_server import Socks5Server
from servers.http_proxy_server import HttpProxyServer
from utils.traffic_logger import TrafficLogger
from core.adblock_manager import AdBlockManager
from core.proxy_analytics import ProxyAnalytics

logger = logging.getLogger("api_server")

_STATIC_DIR = Path(__file__).parent.parent / "static"
_API_PORT = 9090

# ── Global State ──
_engine = None


class ProxyEngine:
    """يجمع كل مكونات البروكسي في كائن واحد."""

    def __init__(self):
        self.manager: ProxyManager = None
        self.failover: FailoverHandler = None
        self.socks5: Socks5Server = None
        self.http_proxy: HttpProxyServer = None
        self.traffic: TrafficLogger = TrafficLogger.get_instance()
        self.loop: asyncio.AbstractEventLoop = None
        self.running = False
        self.starting = False
        self._maintain_task = None
        self._discovery_task = None
        self._fetch_task = None
        # Discovery state
        self.discovery_enabled = True
        self.discovery_paused = False
        self.discovery_round = 0
        self.discovery_checked = 0
        self.discovery_alive_found = 0
        self.discovery_ssl_found = 0
        self.discovery_total_unchecked = 0

    async def start(self):
        """تشغيل محرك البروكسي."""
        if self.running or self.starting:
            return

        self.starting = True
        try:
            # 1. Load proxies
            self.manager = ProxyManager()
            proxies = self.manager.load_proxies()
            if not proxies:
                logger.error("No proxies found!")
                return

            # 2. Detect real IP
            real_ip = await detect_real_ip()
            if real_ip:
                config.REAL_IP = real_ip
            else:
                config.ANONYMITY_CHECK = False

            # 3. Failover
            self.failover = FailoverHandler(self.manager)
            await self.failover.initialize()

            # 4. Start SOCKS5 and HTTP immediately!
            self.socks5 = Socks5Server(self.failover)
            await self.socks5.start()

            self.http_proxy = HttpProxyServer(self.failover)
            await self.http_proxy.start()

            self.running = True

            # 5. Background maintenance and rapid filling
            self._maintain_task = asyncio.create_task(self._initial_and_maintain_pool(proxies))

            # 6. Continuous discovery
            self._discovery_task = asyncio.create_task(self._continuous_discovery())

            # 7. Online proxy fetch
            if getattr(config, 'FETCH_ENABLED', True):
                self._fetch_task = asyncio.create_task(self._online_fetch_loop())

            logger.info("[ENGINE] Servers started instantly! Searching for proxies in background...")
        finally:
            self.starting = False

    async def stop(self):
        """إيقاف محرك البروكسي."""
        if not self.running:
            return

        for task in [self._maintain_task, self._discovery_task, self._fetch_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        if self.socks5:
            await self.socks5.stop()
        if self.http_proxy:
            await self.http_proxy.stop()

        self.running = False
        logger.info("[ENGINE] Proxy engine stopped!")

    async def _initial_and_maintain_pool(self, proxies: list[dict]):
        """Starts by rapidly finding proxies individually, then falls back to normal maintenance loop."""
        try:
            import random
            from core.proxy_checker import check_single_proxy
            from core.proxy_analytics import ProxyAnalytics
            
            analytics = ProxyAnalytics.get_instance()
            proxy_map = {p["id"]: p for p in proxies}
            
            unchecked = proxies.copy()
            random.shuffle(unchecked)
            
            alive_found = 0
            
            # Rapid fill phase
            for start_idx in range(0, len(unchecked), config.BATCH_SIZE):
                if alive_found >= config.MIN_ALIVE_POOL:
                    break
                    
                batch = unchecked[start_idx : start_idx + config.BATCH_SIZE]
                semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_CHECKS)
                
                async def _limited_check(p):
                    async with semaphore:
                        return await check_single_proxy(p)
                        
                tasks = [_limited_check(p) for p in batch]
                
                for coro in asyncio.as_completed(tasks):
                    r = await coro
                    # Update status immediately for this single proxy
                    self.manager.update_status([r])
                    
                    if r["alive"]:
                        alive_found += 1
                        # Force failover to pick it up immediately!
                        await self.failover.refresh_best()
                        logger.info(f"[QUICK] Proxy found & activated! Active count: {alive_found}")
                    
                    try:
                        px = proxy_map.get(r["id"])
                        c = px.get("country", "??") if px else "??"
                        analytics.record_check(r["id"], r["alive"], r.get("response_time_ms"), c)
                    except Exception:
                        pass
                
                if alive_found >= config.MIN_ALIVE_POOL:
                    break
                    
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"[ENGINE] Rapid fill error: {e}")

        # Fall into standard maintenance mode
        await self._maintain_pool()

    async def _maintain_pool(self):
        """حلقة صيانة البروكسيات العادية الاستمرارية."""
        while True:
            await asyncio.sleep(config.RECHECK_INTERVAL_SECONDS)

            # إعادة فحص العاملين
            alive = self.manager.get_alive_proxies()
            if alive:
                # Need to import strictly inside the loop to avoid circular deps if any
                from core.proxy_checker import recheck_alive_proxies
                results = await recheck_alive_proxies(alive)
                self.manager.update_status(results)

            # فرصة ثانية
            retry = self.manager.get_dead_proxies_for_retry()
            if retry:
                from core.proxy_checker import check_batch
                results = await check_batch(retry)
                self.manager.update_status(results)

            # تعبئة النقص
            current_alive = len(self.manager.get_alive_proxies())
            if current_alive < config.MIN_ALIVE_POOL:
                unchecked = self.manager.get_unchecked_proxies(config.BATCH_SIZE)
                if unchecked:
                    from core.proxy_checker import check_batch
                    results = await check_batch(unchecked)
                    self.manager.update_status(results)

            await self.failover.refresh_best()

    async def _continuous_discovery(self):
        """فحص مستمر لجميع البروكسيات بالخلفية."""
        from core.proxy_checker import check_batch

        batch_size = getattr(config, "DISCOVERY_BATCH_SIZE", 20)
        delay = getattr(config, "DISCOVERY_DELAY_SECONDS", 3)

        while True:
            if not self.discovery_enabled:
                await asyncio.sleep(2)
                continue

            self.discovery_round += 1
            self.discovery_checked = 0
            self.discovery_alive_found = 0
            self.discovery_ssl_found = 0

            # حساب عدد البروكسيات غير المفحوصة
            if self.manager:
                all_unchecked = [p for p in self.manager.proxies if p["id"] not in self.manager.status]
                self.discovery_total_unchecked = len(all_unchecked)

            logger.info(f"[DISCOVERY] Round #{self.discovery_round} — {self.discovery_total_unchecked} unchecked")

            while True:
                # تحقق من الإيقاف المؤقت
                while self.discovery_paused:
                    await asyncio.sleep(1)

                if not self.discovery_enabled:
                    break

                # قراءة الإعدادات الحية
                batch_size = getattr(config, "DISCOVERY_BATCH_SIZE", 20)
                delay = getattr(config, "DISCOVERY_DELAY_SECONDS", 3)

                unchecked = self.manager.get_unchecked_proxies(batch_size)
                if not unchecked:
                    break

                results = await check_batch(unchecked)
                self.manager.update_status(results)

                batch_alive = sum(1 for r in results if r["alive"])
                batch_ssl = sum(1 for r in results if r.get("ssl_verified", False))
                self.discovery_checked += len(unchecked)
                self.discovery_alive_found += batch_alive
                self.discovery_ssl_found += batch_ssl

                if batch_alive > 0 and self.failover:
                    await self.failover.refresh_best()

                await asyncio.sleep(delay)

            # انتهت الجولة
            logger.info(
                f"[DISCOVERY] Round #{self.discovery_round} done — "
                f"{self.discovery_checked} checked, {self.discovery_alive_found} alive, "
                f"{self.discovery_ssl_found} SSL"
            )

            if self.manager:
                self.manager.save_sorted_data_file()

            await asyncio.sleep(config.RECHECK_INTERVAL_SECONDS)

    async def _online_fetch_loop(self):
        """جلب بروكسيات من الإنترنت بشكل دوري."""
        from core.proxy_fetcher import ProxyFetcher
        from core.proxy_checker import check_batch

        fetcher = ProxyFetcher.get_instance()

        # سجّل البروكسيات الحالية لمنع التكرار
        if self.manager:
            for p in self.manager.proxies:
                fetcher.add_known(p["ip"], p["port"])

        logger.info(f"[FETCH] Online fetch started — interval: {fetcher.fetch_interval}s")

        while True:
            if not getattr(config, 'FETCH_ENABLED', True):
                await asyncio.sleep(10)
                continue

            try:
                new_proxies = await fetcher.fetch_all()

                if new_proxies:
                    # أضف للمدير
                    added = 0
                    for p in new_proxies:
                        proxy = self.manager.add_custom_proxy(
                            p["ip"], p["port"], p["type"]
                        )
                        if proxy:
                            added += 1

                    fetcher.total_added += added
                    logger.info(
                        f"[FETCH] Added {added} new proxies — "
                        f"checking in batches..."
                    )

                    # فحص البروكسيات الجديدة على دفعات
                    batch_size = getattr(config, "DISCOVERY_BATCH_SIZE", 20)
                    new_ids = {f"custom_{p['ip']}_{p['port']}" for p in new_proxies}
                    to_check = [
                        p for p in self.manager.proxies
                        if p["id"] in new_ids and p["id"] not in self.manager.status
                    ]

                    for i in range(0, len(to_check), batch_size):
                        batch = to_check[i:i + batch_size]
                        results = await check_batch(batch)
                        self.manager.update_status(results)

                        alive = sum(1 for r in results if r["alive"])
                        if alive > 0 and self.failover:
                            await self.failover.refresh_best()

                        await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"[FETCH] Error: {e}")

            interval = getattr(config, "FETCH_INTERVAL_SECONDS", 120)
            await asyncio.sleep(interval)

    def get_status(self) -> dict:
        """حالة السيرفر الحالية."""
        local_ips = []
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = info[4][0]
                if ip not in local_ips and ip != "127.0.0.1":
                    local_ips.append(ip)
        except Exception:
            pass

        current = self.failover.current_proxy if self.failover else None
        active_proxy = None
        if current:
            st = self.manager.get_proxy_status(current["id"])
            spd = st.get("response_time_ms")
            active_proxy = {
                "id": current["id"],
                "ip": current["ip"],
                "port": current["port"],
                "type": current["type"].upper(),
                "speed_ms": spd,
                "ssl_verified": st.get("ssl_verified", False),
                "switches": self.failover.switch_count,
                "manual_locked": self.failover.is_manual_locked,
            }

        pool = self.manager.get_pool_summary() if self.manager else {}

        return {
            "running": self.running,
            "starting": getattr(self, 'starting', False),
            "socks5_port": config.LOCAL_PORT,
            "http_port": config.HTTP_PROXY_PORT,
            "socks5_ok": bool(self.socks5 and getattr(self.socks5, '_server', None)),
            "http_ok": bool(self.http_proxy and getattr(self.http_proxy, '_server', None)),
            "auth_enabled": config.AUTH_ENABLED,
            "auth_user": config.AUTH_USERNAME,
            "auth_pass": config.AUTH_PASSWORD,
            "local_ips": local_ips,
            "pool": pool,
            "active_proxy": active_proxy,
            "socks5_connections": getattr(self.socks5, 'active_connections', 0) if self.socks5 else 0,
            "http_connections": getattr(self.http_proxy, 'active_connections', 0) if self.http_proxy else 0,
            "discovery": {
                "enabled": self.discovery_enabled,
                "paused": self.discovery_paused,
                "round": self.discovery_round,
                "checked": self.discovery_checked,
                "alive_found": self.discovery_alive_found,
                "ssl_found": self.discovery_ssl_found,
                "total_unchecked": self.discovery_total_unchecked,
                "batch_size": getattr(config, 'DISCOVERY_BATCH_SIZE', 20),
                "delay": getattr(config, 'DISCOVERY_DELAY_SECONDS', 3),
            },
            "fetch": self._get_fetch_stats(),
        }

    def _get_fetch_stats(self) -> dict:
        try:
            from core.proxy_fetcher import ProxyFetcher
            return ProxyFetcher.get_instance().get_stats()
        except Exception:
            return {"enabled": False}

    def get_clients(self) -> list:
        """العملاء المتصلون."""
        clients = []
        if self.socks5:
            clients.extend(self.socks5.connected_clients)
        if self.http_proxy:
            clients.extend(self.http_proxy.connected_clients)
        return clients

    def get_proxies(self) -> list:
        """جدول البروكسيات."""
        if not self.manager:
            return []

        current = self.failover.current_proxy if self.failover else None
        data = self.manager.get_dashboard_data()
        result = []
        for item in data[:30]:
            p = item["proxy"]
            st = item["status"]
            result.append({
                "id": p["id"],
                "ip": p["ip"],
                "port": p["port"],
                "type": p["type"].upper(),
                "country": p.get("country", "??"),
                "alive": st.get("alive", False),
                "speed_ms": st.get("response_time_ms"),
                "score": item["score"],
                "failures": st.get("consecutive_failures", 0),
                "ssl_verified": st.get("ssl_verified", False),
                "active": bool(current and p["id"] == current["id"]),
            })
        return result


class APIHandler(SimpleHTTPRequestHandler):
    """HTTP handler for API + static files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(_STATIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # suppress default logging

    def do_GET(self):
        path = unquote(urlparse(self.path).path)

        if path == "/api/status":
            self._json(get_engine().get_status())
        elif path == "/api/clients":
            self._json(get_engine().get_clients())
        elif path == "/api/proxies":
            self._json(get_engine().get_proxies())
        elif path == "/api/traffic":
            tlog = TrafficLogger.get_instance()
            self._json({
                "stats": tlog.get_stats(),
                "recent": tlog.get_recent(50),
                "client_stats": tlog.get_client_stats(),
            })
        elif path == "/api/config":
            self._json(config.get_all_config())
        elif path == "/api/blocklist":
            ab = AdBlockManager.get_instance()
            self._json({
                "stats": ab.get_stats(),
                "rules": ab.get_rules(),
                "whitelist": ab.get_whitelist(),
                "categories": ab.get_categories(),
            })
        elif path == "/api/countries":
            engine = get_engine()
            manager = engine.manager
            if not manager:
                from core.proxy_manager import ProxyManager
                manager = ProxyManager()
                manager.load_proxies()
                
            countries = manager.get_available_countries()
            self._json({
                "countries": countries,
                "current": getattr(config, 'COUNTRY_FILTER', 'GLOBAL'),
            })
        elif path == "/api/analytics":
            pa = ProxyAnalytics.get_instance()
            self._json(pa.get_summary())
        elif path == "/api/analytics/top":
            pa = ProxyAnalytics.get_instance()
            self._json(pa.get_top_proxies(20))
        elif path == "/api/analytics/countries":
            pa = ProxyAnalytics.get_instance()
            self._json(pa.get_country_stats())
        elif path == "/api/discovery":
            e = get_engine()
            self._json({
                "enabled": e.discovery_enabled,
                "paused": e.discovery_paused,
                "round": e.discovery_round,
                "checked": e.discovery_checked,
                "alive_found": e.discovery_alive_found,
                "ssl_found": e.discovery_ssl_found,
                "total_unchecked": e.discovery_total_unchecked,
                "batch_size": getattr(config, 'DISCOVERY_BATCH_SIZE', 20),
                "delay": getattr(config, 'DISCOVERY_DELAY_SECONDS', 3),
            })
        else:
            super().do_GET()

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        body = self._read_body()

        if path == "/api/start":
            self._run_async(get_engine().start())
            self._json({"success": True})
        elif path == "/api/stop":
            self._run_async(get_engine().stop())
            self._json({"success": True})
        elif path == "/api/traffic/clear":
            TrafficLogger.get_instance().clear()
            self._json({"success": True})
        elif path == "/api/blocklist/rules":
            ab = AdBlockManager.get_instance()
            action = body.get("action", "add")
            domain = body.get("domain", "")
            category = body.get("category", "custom")
            if action == "add":
                ok = ab.add_rule(domain, category)
            elif action == "remove":
                ok = ab.remove_rule(domain)
            else:
                ok = False
            self._json({"success": ok})
        elif path == "/api/blocklist/whitelist":
            ab = AdBlockManager.get_instance()
            action = body.get("action", "add")
            domain = body.get("domain", "")
            if action == "add":
                ok = ab.add_whitelist(domain)
            elif action == "remove":
                ok = ab.remove_whitelist(domain)
            else:
                ok = False
            self._json({"success": ok})
        elif path == "/api/blocklist/toggle":
            ab = AdBlockManager.get_instance()
            # Toggle the whole blocker or a specific category
            category = body.get("category")  # None = toggle global
            enabled = body.get("enabled", True)
            if category:
                ab.toggle_category(category, enabled)
            else:
                ab.toggle_enabled(enabled)
            self._json({"success": True})
        elif path == "/api/config":
            changed = config.update_config(body)
            self._json({"success": True, "changed": changed})
        elif path == "/api/discovery/toggle":
            e = get_engine()
            action = body.get("action", "toggle")
            if action == "pause":
                e.discovery_paused = True
            elif action == "resume":
                e.discovery_paused = False
            elif action == "enable":
                e.discovery_enabled = True
                e.discovery_paused = False
            elif action == "disable":
                e.discovery_enabled = False
            self._json({"success": True, "enabled": e.discovery_enabled, "paused": e.discovery_paused})
        elif path == "/api/discovery/config":
            updates = {}
            if "batch_size" in body:
                updates["DISCOVERY_BATCH_SIZE"] = int(body["batch_size"])
            if "delay" in body:
                updates["DISCOVERY_DELAY_SECONDS"] = int(body["delay"])
            if updates:
                config.update_config(updates)
            self._json({"success": True, "batch_size": config.DISCOVERY_BATCH_SIZE, "delay": config.DISCOVERY_DELAY_SECONDS})
        elif path == "/api/proxy/select":
            proxy_id = body.get("id", "")
            e = get_engine()
            if not e.manager or not e.failover:
                self._json({"error": "Engine not running"}, 400)
                return
            proxy = e.manager._proxies_by_id.get(proxy_id)
            if not proxy:
                self._json({"error": "Proxy not found"}, 404)
                return
            self._run_async(e.failover.force_select(proxy), wait=True)
            self._json({"success": True, "selected": proxy_id})
        elif path == "/api/proxy/unlock":
            e = get_engine()
            if e.failover:
                e.failover.unlock_auto()
            self._json({"success": True})
        elif path == "/api/proxy/add":
            e = get_engine()
            if not e.manager:
                self._json({"error": "Engine not running"}, 400)
                return
            ip = body.get("ip", "").strip()
            port = body.get("port", 0)
            ptype = body.get("type", "socks5")
            username = body.get("username") or None
            password = body.get("password") or None
            if not ip or not port:
                self._json({"error": "IP and port required"}, 400)
                return
            proxy = e.manager.add_custom_proxy(ip, int(port), ptype, username, password)
            # فحص البروكسي فوراً
            async def _check_and_activate():
                from core.proxy_checker import check_single_proxy
                result = await check_single_proxy(proxy)
                e.manager.update_status([result])
                if result["alive"]:
                    await e.failover.force_select(proxy)
                return result
            self._run_async(_check_and_activate())
            self._json({"success": True, "id": proxy["id"]})
        else:
            self._json({"error": "Not found"}, 404)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        return json.loads(raw) if raw else {}

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _run_async(self, coro, wait=False):
        """Run async coroutine from sync handler.
        If wait=False, do not block the HTTP thread (prevents UI freezing during scans)."""
        engine = get_engine()
        if engine.loop and engine.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, engine.loop)
            if wait:
                future.result(timeout=30)


def get_engine() -> ProxyEngine:
    global _engine
    if _engine is None:
        _engine = ProxyEngine()
    return _engine


def _run_event_loop(engine: ProxyEngine):
    """Run asyncio event loop in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    engine.loop = loop

    # Do NOT auto-start the engine. Let the user start it via the UI Modal.
    loop.run_forever()


def start_api_server():
    """Start the API server (blocking)."""
    global _engine

    # Ensure static dir exists
    _STATIC_DIR.mkdir(parents=True, exist_ok=True)

    _engine = ProxyEngine()

    # Start async engine in background thread
    engine_thread = threading.Thread(target=_run_event_loop, args=(_engine,), daemon=True)
    engine_thread.start()

    # Wait for the event loop to initialize
    import time
    for _ in range(100):
        if _engine.loop and _engine.loop.is_running():
            break
        time.sleep(0.05)

    # Start HTTP API server
    server = HTTPServer(("127.0.0.1", _API_PORT), APIHandler)
    logger.info(f"[API] Server on http://127.0.0.1:{_API_PORT}")
    server.serve_forever()


def stop_api_server():
    """Stop the engine."""
    if _engine and _engine.loop:
        asyncio.run_coroutine_threadsafe(_engine.stop(), _engine.loop)
