"""
Proxy Redirector — HTTP Proxy Server
سيرفر HTTP Proxy للأجهزة التي لا تدعم SOCKS5 (الهواتف)
يستقبل اتصالات HTTP/HTTPS ويمررها عبر البروكسيات العاملة

يدعم:
  - CONNECT method (أنفاق HTTPS)
  - HTTP forwarding (طلبات HTTP العادية)
  - Basic Auth (مصادقة بكلمة مرور)
"""

import asyncio
import base64
import logging
import time
from typing import Optional
from urllib.parse import urlparse

from python_socks.async_.asyncio import Proxy
from python_socks import ProxyType

from failover_handler import FailoverHandler
from traffic_logger import TrafficLogger
import config

logger = logging.getLogger("http_proxy")


def _get_upstream_proxy_type(type_str: str) -> ProxyType:
    mapping = {
        "socks5": ProxyType.SOCKS5,
        "socks4": ProxyType.SOCKS4,
        "https": ProxyType.HTTP,
        "http": ProxyType.HTTP,
    }
    return mapping.get(type_str.lower(), ProxyType.SOCKS5)


class HttpProxyServer:
    def __init__(self, failover: FailoverHandler):
        self.failover = failover
        self._server: Optional[asyncio.AbstractServer] = None
        self._active_connections = 0
        self._last_no_proxy_log = 0
        # تتبع العملاء المتصلين
        self._clients: dict[int, dict] = {}
        self._client_counter = 0

    @property
    def active_connections(self) -> int:
        return self._active_connections

    @property
    def connected_clients(self) -> list[dict]:
        return list(self._clients.values())

    async def start(self):
        self._server = await asyncio.start_server(
            self._handle_client,
            config.LOCAL_HOST,
            config.HTTP_PROXY_PORT,
        )
        logger.info(
            f"[HTTP-PROXY] Listening on {config.LOCAL_HOST}:{config.HTTP_PROXY_PORT}"
        )

    async def stop(self):
        if self._server:
            self._server.close()
            try:
                await asyncio.wait_for(self._server.wait_closed(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            except Exception:
                pass
            logger.info("[HTTP-PROXY] Stopped")

    def _is_whitelisted(self, client_ip: str) -> bool:
        """هل عنوان العميل في القائمة البيضاء؟"""
        for prefix in config.AUTH_WHITELIST:
            if client_ip.startswith(prefix):
                return True
        return False

    def _check_auth(self, headers: dict, client_ip: str) -> bool:
        """التحقق من المصادقة — تُتخطى للشبكة المحلية."""
        if not config.AUTH_ENABLED:
            return True

        # الأجهزة المحلية (الهواتف) مسموح لها بدون مصادقة
        if self._is_whitelisted(client_ip):
            return True

        auth_header = headers.get("proxy-authorization", "")
        if not auth_header:
            return False

        try:
            scheme, encoded = auth_header.split(" ", 1)
            if scheme.lower() != "basic":
                return False
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
            return (
                username == config.AUTH_USERNAME
                and password == config.AUTH_PASSWORD
            )
        except Exception:
            return False

    async def _handle_client(self, reader, writer):
        self._active_connections += 1
        self._client_counter += 1
        client_id = self._client_counter

        try:
            # معرفة IP العميل
            peername = writer.get_extra_info("peername")
            client_ip = peername[0] if peername else "unknown"

            # قراءة السطر الأول من الطلب
            first_line = await asyncio.wait_for(
                reader.readline(), timeout=15
            )
            if not first_line:
                return

            first_line_str = first_line.decode("utf-8", errors="replace").strip()
            parts = first_line_str.split(" ")
            if len(parts) < 3:
                await self._send_error(writer, 400, "Bad Request")
                return

            method = parts[0].upper()
            target = parts[1]

            # تسجيل العميل
            display_target = target
            if method == "CONNECT":
                display_target = target
            else:
                from urllib.parse import urlparse as _urlparse
                _p = _urlparse(target)
                display_target = _p.hostname or target
                if _p.port:
                    display_target += f":{_p.port}"

            self._clients[client_id] = {
                "ip": client_ip,
                "target": display_target,
                "protocol": "HTTP",
            }

            # قراءة الهيدرز
            headers = {}
            raw_headers = b""
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=10)
                raw_headers += line
                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    break
                if ":" in line_str:
                    key, value = line_str.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

            # التحقق من المصادقة (يُتخطى للشبكة المحلية)
            if not self._check_auth(headers, client_ip):
                logger.warning(f"[HTTP-PROXY] Auth failed from {client_ip}")
                await self._send_auth_required(writer)
                return

            if method == "CONNECT":
                await self._handle_connect(target, client_ip, reader, writer)
            else:
                await self._handle_http(
                    method, target, client_ip, headers, raw_headers,
                    first_line, reader, writer
                )

        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        finally:
            self._active_connections -= 1
            self._clients.pop(client_id, None)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _handle_connect(self, target, client_ip, reader, writer):
        """
        معالجة CONNECT — أنفاق HTTPS
        الهاتف يرسل: CONNECT example.com:443 HTTP/1.1
        نربط بالهدف عبر البروكسي ونعيد: HTTP/1.1 200
        """
        # تحليل الهدف
        if ":" in target:
            host, port_str = target.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 443
        else:
            host = target
            port = 443

        tlog = TrafficLogger.get_instance()

        # الاتصال عبر البروكسي
        up_reader, up_writer = await self._connect_via_proxy(host, port)
        if up_reader is None:
            tlog.log_request(client_ip, "HTTP", f"{host}:{port}", "CONNECT", "failed")
            await self._send_error(writer, 502, "Bad Gateway")
            return

        tlog.log_request(client_ip, "HTTP", f"{host}:{port}", "CONNECT", "success")

        # رد بالنجاح
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()

        # نقل البيانات بالاتجاهين
        await self._relay(reader, writer, up_reader, up_writer)

    async def _handle_http(
        self, method, target, client_ip, headers, raw_headers,
        first_line, reader, writer
    ):
        """
        معالجة طلبات HTTP العادية (GET, POST, إلخ) + WebSocket (WS)
        الهاتف يرسل: GET http://example.com/path HTTP/1.1
        نوصل الطلب عبر البروكسي
        """
        # تحليل URL
        parsed = urlparse(target)
        host = parsed.hostname
        port = parsed.port or 80

        if not host:
            await self._send_error(writer, 400, "Bad Request - No Host")
            return

        # هل هذا طلب ترقية WebSocket؟
        is_websocket = (
            headers.get("upgrade", "").lower() == "websocket"
        )

        tlog = TrafficLogger.get_instance()

        # الاتصال عبر البروكسي
        up_reader, up_writer = await self._connect_via_proxy(host, port)
        if up_reader is None:
            tlog.log_request(client_ip, "HTTP", f"{host}:{port}", method, "failed")
            await self._send_error(writer, 502, "Bad Gateway")
            return

        tlog.log_request(client_ip, "HTTP", f"{host}:{port}", method, "success")

        # إعادة بناء الطلب مع مسار نسبي
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        new_first_line = f"{method} {path} HTTP/1.1\r\n"
        up_writer.write(new_first_line.encode("utf-8"))

        # إرسال الهيدرز (بدون proxy-authorization)
        for key, value in headers.items():
            if key.lower() in ("proxy-authorization", "proxy-connection"):
                continue
            # لا تعدّل Connection/Upgrade في حالة WebSocket
            if not is_websocket and key.lower() == "connection":
                continue
            up_writer.write(f"{key}: {value}\r\n".encode("utf-8"))

        # إذا ليس WebSocket، أضف Connection: close
        if not is_websocket:
            up_writer.write(b"Connection: close\r\n")

        up_writer.write(b"\r\n")
        await up_writer.drain()

        # إرسال الجسم إن وجد
        content_length = headers.get("content-length")
        if content_length:
            try:
                body_len = int(content_length)
                body = await asyncio.wait_for(
                    reader.readexactly(body_len), timeout=30
                )
                up_writer.write(body)
                await up_writer.drain()
            except Exception:
                pass

        if is_websocket:
            # WebSocket: نقل بالاتجاهين (مثل CONNECT)
            await self._relay(reader, writer, up_reader, up_writer)
        else:
            # HTTP عادي: نقل الرد فقط
            await self._relay_response(up_reader, writer, up_writer)

    async def _connect_via_proxy(self, target_host, target_port):
        """الاتصال بالهدف عبر قائمة البروكسيات العاملة."""

        alive_list = self.failover.manager.get_alive_proxies()

        if not alive_list:
            now = time.time()
            if now - self._last_no_proxy_log > 10:
                logger.error("[HTTP-PROXY] No alive proxies available")
                self._last_no_proxy_log = now
            return (None, None)

        # ابدأ من البروكسي النشط
        current = await self.failover.get_active_proxy()
        ordered = []
        if current:
            ordered.append(current)
            for p in alive_list:
                if p["id"] != current["id"]:
                    ordered.append(p)
        else:
            ordered = alive_list

        for proxy_data in ordered[:5]:
            try:
                proxy_type = _get_upstream_proxy_type(proxy_data["type"])
                proxy = Proxy(
                    proxy_type=proxy_type,
                    host=proxy_data["ip"],
                    port=proxy_data["port"],
                    username=proxy_data.get("username"),
                    password=proxy_data.get("password"),
                    rdns=True,
                )

                sock = await asyncio.wait_for(
                    proxy.connect(
                        dest_host=target_host, dest_port=target_port
                    ),
                    timeout=config.CHECK_TIMEOUT_SECONDS,
                )

                up_reader, up_writer = await asyncio.open_connection(sock=sock)

                if current and proxy_data["id"] != current["id"]:
                    await self.failover.suggest_switch(proxy_data)

                return (up_reader, up_writer)

            except Exception:
                continue

        return (None, None)

    async def _relay(self, client_reader, client_writer, up_reader, up_writer):
        """نقل البيانات بالاتجاهين (للأنفاق CONNECT)."""

        async def _pipe(src, dst):
            try:
                while True:
                    data = await src.read(8192)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
            except (ConnectionResetError, BrokenPipeError, OSError):
                pass
            finally:
                try:
                    dst.close()
                except Exception:
                    pass

        await asyncio.gather(
            _pipe(client_reader, up_writer),
            _pipe(up_reader, client_writer),
        )

    async def _relay_response(self, up_reader, client_writer, up_writer):
        """نقل رد السيرفر البعيد إلى العميل."""
        try:
            while True:
                data = await up_reader.read(8192)
                if not data:
                    break
                client_writer.write(data)
                await client_writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError):
            pass
        finally:
            try:
                up_writer.close()
            except Exception:
                pass

    async def _send_error(self, writer, code, message):
        """إرسال رد خطأ HTTP."""
        body = f"<h1>{code} {message}</h1>"
        response = (
            f"HTTP/1.1 {code} {message}\r\n"
            f"Content-Type: text/html\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        try:
            writer.write(response.encode("utf-8"))
            await writer.drain()
        except Exception:
            pass

    async def _send_auth_required(self, writer):
        """إرسال طلب مصادقة 407."""
        body = "<h1>407 Proxy Authentication Required</h1>"
        response = (
            "HTTP/1.1 407 Proxy Authentication Required\r\n"
            'Proxy-Authenticate: Basic realm="Proxy Redirector"\r\n'
            "Content-Type: text/html\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{body}"
        )
        try:
            writer.write(response.encode("utf-8"))
            await writer.drain()
        except Exception:
            pass
