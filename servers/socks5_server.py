"""
Proxy Redirector — SOCKS5 Local Server v2
التغيير الرئيسي: السيرفر لا يقتل البروكسيات.
يجرب القائمة بصمت — فقط الـ checker يحدد الحالة.
"""

import asyncio
import struct
import logging
from typing import Optional

from python_socks.async_.asyncio import Proxy
from python_socks import ProxyType

from core.failover_handler import FailoverHandler
from utils.traffic_logger import TrafficLogger
from core.adblock_manager import AdBlockManager
import config

logger = logging.getLogger("socks5_server")

# ── ثوابت SOCKS5 ──
SOCKS5_VER = 0x05
AUTH_NONE = 0x00
AUTH_USERPASS = 0x02
AUTH_NO_ACCEPTABLE = 0xFF
AUTH_USERPASS_VER = 0x01
CMD_CONNECT = 0x01
ATYP_IPV4 = 0x01
ATYP_DOMAIN = 0x03
ATYP_IPV6 = 0x04
REP_SUCCESS = 0x00
REP_GENERAL_FAILURE = 0x01
REP_HOST_UNREACHABLE = 0x04


def _get_upstream_proxy_type(type_str: str) -> ProxyType:
    mapping = {
        "socks5": ProxyType.SOCKS5,
        "socks4": ProxyType.SOCKS4,
        "https": ProxyType.HTTP,
        "http": ProxyType.HTTP,
    }
    return mapping.get(type_str.lower(), ProxyType.SOCKS5)


class Socks5Server:
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
            config.LOCAL_PORT,
        )
        logger.info(
            f"[SERVER] SOCKS5 listening on {config.LOCAL_HOST}:{config.LOCAL_PORT}"
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
            logger.info("[SERVER] Stopped")

    async def _handle_client(self, reader, writer):
        self._active_connections += 1
        self._client_counter += 1
        client_id = self._client_counter
        peername = writer.get_extra_info("peername")
        client_ip = peername[0] if peername else "unknown"

        try:
            if not await self._socks5_handshake(reader, writer):
                return

            target = await self._read_connect_request(reader, writer)
            if target is None:
                return

            target_host, target_port = target

            # تسجيل العميل
            self._clients[client_id] = {
                "ip": client_ip,
                "target": f"{target_host}:{target_port}",
                "protocol": "SOCKS5",
            }

            # ── فحص حظر الإعلانات ──
            tlog = TrafficLogger.get_instance()
            adblocker = AdBlockManager.get_instance()
            if adblocker.is_blocked(target_host):
                tlog.log_request(client_ip, "SOCKS5", f"{target_host}:{target_port}", "CONNECT", "blocked")
                await self._send_error_reply(writer, REP_GENERAL_FAILURE)
                return

            # الاتصال عبر البروكسي — بدون قتل أي بروكسي
            up_reader, up_writer = await self._connect_via_proxy(
                target_host, target_port, writer
            )
            if up_reader is None:
                tlog.log_request(client_ip, "SOCKS5", f"{target_host}:{target_port}", "CONNECT", "failed")
                return

            tlog.log_request(client_ip, "SOCKS5", f"{target_host}:{target_port}", "CONNECT", "success")
            await self._send_success_reply(writer)
            await self._relay(reader, writer, up_reader, up_writer)

        except (ConnectionResetError, BrokenPipeError, OSError):
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

    def _is_whitelisted(self, client_ip: str) -> bool:
        """هل عنوان العميل في القائمة البيضاء؟"""
        for prefix in config.AUTH_WHITELIST:
            if client_ip.startswith(prefix):
                return True
        return False

    async def _socks5_handshake(self, reader, writer) -> bool:
        try:
            # معرفة IP العميل
            peername = writer.get_extra_info("peername")
            client_ip = peername[0] if peername else "unknown"

            data = await asyncio.wait_for(reader.read(256), timeout=10)
            if len(data) < 3 or data[0] != SOCKS5_VER:
                writer.close()
                return False

            nmethods = data[1]
            methods = data[2:2 + nmethods]

            # هل العميل من الشبكة المحلية؟ → بدون مصادقة
            if config.AUTH_ENABLED and not self._is_whitelisted(client_ip):
                # مطلوب مصادقة — هل العميل يدعمها؟
                if AUTH_USERPASS not in methods:
                    writer.write(struct.pack("BB", SOCKS5_VER, AUTH_NO_ACCEPTABLE))
                    await writer.drain()
                    writer.close()
                    return False

                # اطلب مصادقة باسم مستخدم وكلمة مرور
                writer.write(struct.pack("BB", SOCKS5_VER, AUTH_USERPASS))
                await writer.drain()

                # استقبال بيانات المصادقة (RFC 1929)
                auth_data = await asyncio.wait_for(reader.read(513), timeout=10)
                if len(auth_data) < 4 or auth_data[0] != AUTH_USERPASS_VER:
                    writer.write(struct.pack("BB", AUTH_USERPASS_VER, 0x01))  # فشل
                    await writer.drain()
                    writer.close()
                    return False

                ulen = auth_data[1]
                username = auth_data[2:2 + ulen].decode("utf-8", errors="replace")
                plen = auth_data[2 + ulen]
                password = auth_data[3 + ulen:3 + ulen + plen].decode("utf-8", errors="replace")

                if username == config.AUTH_USERNAME and password == config.AUTH_PASSWORD:
                    writer.write(struct.pack("BB", AUTH_USERPASS_VER, 0x00))  # نجاح
                    await writer.drain()
                    logger.info(f"[AUTH] Client {client_ip} authenticated successfully")
                else:
                    writer.write(struct.pack("BB", AUTH_USERPASS_VER, 0x01))  # فشل
                    await writer.drain()
                    logger.warning(f"[AUTH] Authentication failed from {client_ip}")
                    writer.close()
                    return False
            else:
                # بدون مصادقة (شبكة محلية أو AUTH_ENABLED=False)
                writer.write(struct.pack("BB", SOCKS5_VER, AUTH_NONE))
                await writer.drain()

            return True
        except Exception:
            return False

    async def _read_connect_request(self, reader, writer):
        try:
            data = await asyncio.wait_for(reader.read(256), timeout=10)
            if len(data) < 7 or data[0] != SOCKS5_VER or data[1] != CMD_CONNECT:
                await self._send_error_reply(writer, REP_GENERAL_FAILURE)
                return None

            atyp = data[3]
            if atyp == ATYP_IPV4:
                host = ".".join(str(b) for b in data[4:8])
                port = struct.unpack("!H", data[8:10])[0]
            elif atyp == ATYP_DOMAIN:
                dlen = data[4]
                host = data[5:5 + dlen].decode("ascii")
                port = struct.unpack("!H", data[5 + dlen:7 + dlen])[0]
            elif atyp == ATYP_IPV6:
                raw = data[4:20]
                host = ":".join(f"{raw[i]:02x}{raw[i+1]:02x}" for i in range(0, 16, 2))
                port = struct.unpack("!H", data[20:22])[0]
            else:
                await self._send_error_reply(writer, REP_GENERAL_FAILURE)
                return None

            return (host, port)
        except Exception:
            return None

    async def _connect_via_proxy(self, target_host, target_port, client_writer):
        """
        المنطق الجديد:
        - أحضر قائمة البروكسيات العاملة
        - جرب كل واحد بالترتيب (أفضلهم أولاً) 
        - أول واحد ينجح = استخدمه
        - لا تقتل أي بروكسي ولا تغير الـ active proxy
        - فقط أبلغ الـ failover بفشل الحالي (بدون قتل)
        """
        import time

        # أحضر كل البروكسيات العاملة
        alive_list = self.failover.manager.get_alive_proxies()

        if not alive_list:
            # حماية من سيل الرسائل: رسالة واحدة كل 10 ثوان
            now = time.time()
            if now - self._last_no_proxy_log > 10:
                logger.error("[CONN] No alive proxies available")
                self._last_no_proxy_log = now
            await self._send_error_reply(client_writer, REP_HOST_UNREACHABLE)
            return (None, None)

        # ابدأ من البروكسي النشط، ثم جرب الباقي
        current = await self.failover.get_active_proxy()
        ordered = []
        if current:
            ordered.append(current)
            for p in alive_list:
                if p["id"] != current["id"]:
                    ordered.append(p)
        else:
            ordered = alive_list

        # جرب كل بروكسي — بدون قتل
        for proxy_data in ordered[:5]:  # أقصى 5 محاولات
            try:
                proxy_type = _get_upstream_proxy_type(proxy_data["type"])
                proxy = Proxy(
                    proxy_type=proxy_type,
                    host=proxy_data["ip"],
                    port=proxy_data["port"],
                    username=proxy_data.get("username"),
                    password=proxy_data.get("password"),
                    rdns=True,  # ← DNS يتم حله عن بُعد عبر البروكسي (يمنع تسريب DNS)
                )

                sock = await asyncio.wait_for(
                    proxy.connect(dest_host=target_host, dest_port=target_port),
                    timeout=config.CHECK_TIMEOUT_SECONDS,
                )

                up_reader, up_writer = await asyncio.open_connection(sock=sock)

                # نجح! إذا ليس البروكسي النشط، اقترح التبديل
                if current and proxy_data["id"] != current["id"]:
                    await self.failover.suggest_switch(proxy_data)

                return (up_reader, up_writer)

            except Exception:
                # فشل — لا تقتله، فقط جرب التالي
                continue

        # كل المحاولات فشلت
        await self._send_error_reply(client_writer, REP_HOST_UNREACHABLE)
        return (None, None)

    async def _send_success_reply(self, writer):
        reply = struct.pack("!BBBB4sH", SOCKS5_VER, REP_SUCCESS, 0x00,
                            ATYP_IPV4, b"\x00\x00\x00\x00", 0)
        writer.write(reply)
        await writer.drain()

    async def _send_error_reply(self, writer, code):
        try:
            reply = struct.pack("!BBBB4sH", SOCKS5_VER, code, 0x00,
                                ATYP_IPV4, b"\x00\x00\x00\x00", 0)
            writer.write(reply)
            await writer.drain()
        except Exception:
            pass

    async def _relay(self, client_reader, client_writer, up_reader, up_writer):
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
