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
from proxy_manager import ProxyManager
from proxy_checker import find_alive_proxies, recheck_alive_proxies, check_batch, detect_real_ip
from failover_handler import FailoverHandler
from socks5_server import Socks5Server
from http_proxy_server import HttpProxyServer
from traffic_logger import TrafficLogger

logger = logging.getLogger("api_server")

_STATIC_DIR = Path(__file__).parent / "static"
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
        self._maintain_task = None

    async def start(self):
        """تشغيل محرك البروكسي."""
        if self.running:
            return

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

        # 3. Find alive proxies
        results = await find_alive_proxies(proxies, needed=config.MIN_ALIVE_POOL)
        self.manager.update_status(results)

        # 4. Failover
        self.failover = FailoverHandler(self.manager)
        await self.failover.initialize()

        # 5. Start SOCKS5
        self.socks5 = Socks5Server(self.failover)
        await self.socks5.start()

        # 6. Start HTTP Proxy
        self.http_proxy = HttpProxyServer(self.failover)
        await self.http_proxy.start()

        self.running = True

        # 7. Background maintenance
        self._maintain_task = asyncio.create_task(self._maintain_pool())

        logger.info("[ENGINE] Proxy engine started!")

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

    async def _maintain_pool(self):
        """حلقة صيانة البروكسيات."""
        while True:
            await asyncio.sleep(config.RECHECK_INTERVAL_SECONDS)

            # إعادة فحص العاملين
            alive = self.manager.get_alive_proxies()
            if alive:
                results = await recheck_alive_proxies(alive)
                self.manager.update_status(results)

            # فرصة ثانية
            retry = self.manager.get_dead_proxies_for_retry()
            if retry:
                results = await check_batch(retry)
                self.manager.update_status(results)

            # تعبئة النقص
            current_alive = len(self.manager.get_alive_proxies())
            if current_alive < config.MIN_ALIVE_POOL:
                unchecked = self.manager.get_unchecked_proxies(config.BATCH_SIZE)
                if unchecked:
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
            "socks5_port": config.LOCAL_PORT,
            "http_port": config.HTTP_PROXY_PORT,
            "socks5_ok": bool(self.socks5 and self.socks5._server),
            "http_ok": bool(self.http_proxy and self.http_proxy._server),
            "local_ips": local_ips,
            "auth_enabled": config.AUTH_ENABLED,
            "auth_user": config.AUTH_USERNAME,
            "auth_pass": config.AUTH_PASSWORD,
            "active_proxy": active_proxy,
            "pool": pool,
            "socks5_connections": self.socks5.active_connections if self.socks5 else 0,
            "http_connections": self.http_proxy.active_connections if self.http_proxy else 0,
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
            self._json({
                "local_port": config.LOCAL_PORT,
                "http_port": config.HTTP_PROXY_PORT,
                "auth_enabled": config.AUTH_ENABLED,
                "auth_user": config.AUTH_USERNAME,
                "auth_pass": config.AUTH_PASSWORD,
                "whitelist": config.AUTH_WHITELIST,
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

    def _run_async(self, coro):
        """Run async coroutine from sync handler."""
        engine = get_engine()
        if engine.loop and engine.loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, engine.loop).result(timeout=30)


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

    # Auto-start the proxy engine
    loop.run_until_complete(engine.start())
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

    # Wait for engine to be ready
    import time
    for _ in range(100):
        if _engine.loop and _engine.running:
            break
        time.sleep(0.1)

    # Start HTTP API server
    server = HTTPServer(("127.0.0.1", _API_PORT), APIHandler)
    logger.info(f"[API] Server on http://127.0.0.1:{_API_PORT}")
    server.serve_forever()


def stop_api_server():
    """Stop the engine."""
    if _engine and _engine.loop:
        asyncio.run_coroutine_threadsafe(_engine.stop(), _engine.loop)
