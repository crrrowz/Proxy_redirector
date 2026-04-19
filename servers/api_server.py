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

            logger.info("[ENGINE] Servers started instantly! Searching for proxies in background...")
        finally:
            self.starting = False

    async def stop(self):
        """إيقاف محرك البروكسي."""
        if not self.running:
            return

        if self._maintain_task:
            self._maintain_task.cancel()
            try:
                await self._maintain_task
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
                "ip": current["ip"],
                "port": current["port"],
                "type": current["type"].upper(),
                "speed_ms": spd,
                "switches": self.failover.switch_count,
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
        }

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
                "ip": p["ip"],
                "port": p["port"],
                "type": p["type"].upper(),
                "country": p.get("country", "??"),
                "alive": st.get("alive", False),
                "speed_ms": st.get("response_time_ms"),
                "score": item["score"],
                "failures": st.get("consecutive_failures", 0),
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
