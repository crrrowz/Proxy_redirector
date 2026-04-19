"""
Proxy Redirector — Main Entry Point v2
المنطق:
  1. البحث السريع عن 3 بروكسيات (بالدفعات 50)
  2. تشغيل SOCKS5 فوراً
  3. خلفية: إعادة فحص العاملين + فرصة ثانية للميتين + تعبئة النقص
"""

import asyncio
import os
import sys
import io
import logging
import socket

# ── إصلاح ترميز ويندوز ──
if os.name == "nt":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

import config
from core.proxy_manager import ProxyManager
from core.proxy_checker import find_alive_proxies, recheck_alive_proxies, check_batch, detect_real_ip
from core.failover_handler import FailoverHandler
from servers.socks5_server import Socks5Server
from servers.http_proxy_server import HttpProxyServer
from utils.traffic_logger import TrafficLogger

# ── Logging ──
LOG_FORMAT = "%(asctime)s | %(name)-16s | %(levelname)-7s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("python_socks").setLevel(logging.WARNING)
logger = logging.getLogger("main")


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────
W = 74  # عرض الصندوق الداخلي

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def _box_line(text: str, pad: int = W) -> str:
    """سطر داخل صندوق مع محاذاة تلقائية."""
    return f"  ║  {text:<{pad - 4}}║"


def _section_header(title: str) -> list[str]:
    """رأس قسم جديد."""
    return [
        f"  ╠{'═' * W}╣",
        f"  ║  {title:<{W - 4}}║",
        f"  ╠{'─' * W}╣",
    ]


def _get_local_ips() -> list[str]:
    """عناوين IP المحلية."""
    try:
        ips = []
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and ip != "127.0.0.1":
                ips.append(ip)
        return ips
    except Exception:
        return []


def render_dashboard(
    manager: ProxyManager,
    failover: FailoverHandler,
    server: Socks5Server,
    http_proxy: HttpProxyServer,
    status_msg: str = "",
):
    clear_screen()

    current = failover.current_proxy
    pool = manager.get_pool_summary()
    local_ips = _get_local_ips()

    lines = []

    # ╔══════════════════════════════════════════╗
    # ║              HEADER                       ║
    # ╚══════════════════════════════════════════╝
    lines.append("")
    lines.append(f"  ╔{'═' * W}╗")
    lines.append(f"  ║{'Proxy Redirector v2.0 — Network Edition':^{W}}║")
    lines.append(f"  ╠{'═' * W}╣")

    # ── القسم 1: معلومات السيرفر ──
    lines.extend(_section_header("🔌  SERVER INFO"))

    srv_s = "● ON " if server._server else "✗ OFF"
    http_s = "● ON " if http_proxy._server else "✗ OFF"
    lines.append(_box_line(f"SOCKS5  →  0.0.0.0:{config.LOCAL_PORT}  [{srv_s}]"))
    lines.append(_box_line(f"HTTP    →  0.0.0.0:{config.HTTP_PROXY_PORT}  [{http_s}]   (للهواتف)"))

    if local_ips:
        lines.append(_box_line(""))
        lines.append(_box_line("Network Access:"))
        for ip in local_ips:
            lines.append(_box_line(f"  • {ip}:{config.LOCAL_PORT}  (SOCKS5)"))
            lines.append(_box_line(f"  • {ip}:{config.HTTP_PROXY_PORT}  (HTTP — phones)"))

    lines.append(_box_line(""))
    if config.AUTH_ENABLED:
        lines.append(_box_line(f"Auth: {config.AUTH_USERNAME} / {config.AUTH_PASSWORD}  (local network whitelisted)"))
    else:
        lines.append(_box_line("Auth: OFF"))

    # Active proxy
    lines.append(_box_line(""))
    if current:
        st = manager.get_proxy_status(current["id"])
        spd = st.get("response_time_ms")
        spd_s = f"{spd:.0f}ms" if spd else "--"
        lines.append(_box_line(
            f"⚡ Active: {current['ip']}:{current['port']} "
            f"({current['type'].upper()})  {spd_s}  │  Switches: {failover.switch_count}"
        ))
    else:
        lines.append(_box_line("⚡ Active: -- searching..."))

    # ── القسم 2: العملاء المتصلون ──
    all_clients = server.connected_clients + http_proxy.connected_clients
    total_conns = server.active_connections + http_proxy.active_connections
    lines.extend(_section_header(
        f"👥  CONNECTED CLIENTS ({total_conns})"
        f"   [SOCKS5: {server.active_connections}  HTTP: {http_proxy.active_connections}]"
    ))

    if all_clients:
        for c in all_clients[:10]:
            proto = c["protocol"]
            ip = c["ip"]
            target = c["target"]
            # اختصار الهدف إذا طويل
            if len(target) > 35:
                target = target[:32] + "..."
            lines.append(_box_line(f"  {ip:<18s} → {proto:<6s} │ {target}"))
        if len(all_clients) > 10:
            lines.append(_box_line(f"  ... +{len(all_clients) - 10} more"))
    else:
        lines.append(_box_line("  No active connections"))

    # ── القسم 3: حالة المجموعة ──
    lines.extend(_section_header(
        f"📊  POOL STATUS   "
        f"[ {pool['alive']} alive │ {pool['dead_retryable']} retry │ "
        f"{pool['blacklisted']} blocked │ {pool['unchecked']} unchecked ]"
    ))

    # جدول البروكسيات
    hdr = f"{'#':>3}  {'IP:Port':<22} {'Type':<7} {'Status':<7} {'Speed':>7} {'Score':>6} {'Fail':>5}"
    lines.append(_box_line(hdr))
    lines.append(f"  ║  {'─' * (W - 4)}║")

    data = manager.get_dashboard_data()
    for i, item in enumerate(data[:12], 1):
        p = item["proxy"]
        st = item["status"]
        score = item["score"]

        addr = f"{p['ip']}:{p['port']}"
        ptype = p["type"].upper()
        alive = st.get("alive", False)
        status_s = " ● UP " if alive else " ✗ DN "
        spd = st.get("response_time_ms")
        spd_s = f"{spd:>5.0f}ms" if spd else "    -- "
        fails = st.get("consecutive_failures", 0)
        marker = "►" if current and p["id"] == current["id"] else " "

        row = (
            f"{marker}{i:>2}  {addr:<22} {ptype:<7} {status_s} {spd_s} {score:>6.1f} {fails:>5d}"
        )
        lines.append(_box_line(row))

    # ── القسم 4: سجل الحركة ──
    tlog = TrafficLogger.get_instance()
    tstats = tlog.get_stats()
    lines.extend(_section_header(
        f"📝  TRAFFIC LOG   "
        f"[ {tstats['total_requests']} requests │ {tstats['total_bytes_human']} │ "
        f"{tstats['unique_clients']} clients ]"
    ))

    recent = tlog.get_recent(8)
    if recent:
        for r in reversed(recent):
            t = r['time']
            ip = r['client_ip']
            proto = r['protocol']
            method = r['method']
            target = r['target']
            status = '✓' if r['status'] == 'success' else '✗'
            # اختصار الهدف
            if len(target) > 28:
                target = target[:25] + "..."
            lines.append(_box_line(
                f"  {t}  {status} {ip:<16s} {proto:<6s} {method:<8s} {target}"
            ))
    else:
        lines.append(_box_line("  No traffic yet"))

    # ── Footer ──
    lines.append(f"  ╠{'═' * W}╣")

    if status_msg:
        msg = status_msg[:W - 8]
        lines.append(_box_line(f"📡 {msg}"))
    else:
        lines.append(_box_line(""))

    lines.append(f"  ╠{'─' * W}╣")
    lines.append(_box_line("Ctrl+C to stop"))
    lines.append(f"  ╚{'═' * W}╝")
    lines.append("")

    print("\n".join(lines), flush=True)


# ──────────────────────────────────────────────
# Background pool maintenance with second chances
# ──────────────────────────────────────────────
async def maintain_pool(
    manager: ProxyManager,
    failover: FailoverHandler,
    server: Socks5Server,
    http_proxy: HttpProxyServer,
):
    """
    حلقة صيانة المجموعة:
    1. إعادة فحص العاملين (هل ما زالوا حيين؟)
    2. فرصة ثانية: إعادة فحص الميتين المؤهلين
    3. إذا المجموعة ناقصة: فحص بروكسيات جديدة
    """
    cycle = 0

    while True:
        await asyncio.sleep(config.RECHECK_INTERVAL_SECONDS)
        cycle += 1

        # ═══════════════════════════════════════
        # الخطوة 1: إعادة فحص العاملين
        # ═══════════════════════════════════════
        alive_proxies = manager.get_alive_proxies()
        if alive_proxies:
            render_dashboard(
                manager, failover, server, http_proxy,
                f"Cycle #{cycle}: Rechecking {len(alive_proxies)} alive proxies..."
            )
            results = await recheck_alive_proxies(alive_proxies)
            manager.update_status(results)

        # ═══════════════════════════════════════
        # الخطوة 2: فرصة ثانية للميتين
        # ═══════════════════════════════════════
        retry_list = manager.get_dead_proxies_for_retry()
        if retry_list:
            render_dashboard(
                manager, failover, server, http_proxy,
                f"Cycle #{cycle}: Retrying {len(retry_list)} dead proxies (second chance)..."
            )
            logger.info(
                f"[RETRY] Giving second chance to {len(retry_list)} dead proxies"
            )
            retry_results = await check_batch(retry_list)
            manager.update_status(retry_results)

            revived = sum(1 for r in retry_results if r["alive"])
            if revived > 0:
                logger.info(f"[RETRY] {revived} proxies came back to life!")

        # ═══════════════════════════════════════
        # الخطوة 3: تعبئة النقص
        # ═══════════════════════════════════════
        current_alive = len(manager.get_alive_proxies())

        if current_alive < config.MIN_ALIVE_POOL:
            needed = config.MIN_ALIVE_POOL - current_alive
            logger.info(
                f"[POOL] {current_alive}/{config.MIN_ALIVE_POOL} alive. "
                f"Finding {needed} more..."
            )

            render_dashboard(
                manager, failover, server, http_proxy,
                f"Pool low ({current_alive}/{config.MIN_ALIVE_POOL}). Searching..."
            )

            # أولاً: جرب بروكسيات لم تُفحص بعد
            unchecked = manager.get_unchecked_proxies(config.BATCH_SIZE)
            if unchecked:
                results = await check_batch(unchecked)
                manager.update_status(results)

            # إذا لا يزال ناقص وما في جديد: جرب الميتين بعنف
            current_alive = len(manager.get_alive_proxies())
            if current_alive < config.MIN_ALIVE_POOL and not unchecked:
                all_retry = manager.get_dead_proxies_for_retry()
                if all_retry:
                    results = await check_batch(all_retry)
                    manager.update_status(results)

        # ═══════════════════════════════════════
        # تحديث Failover واختيار الأفضل
        # ═══════════════════════════════════════
        await failover.refresh_best()

        pool = manager.get_pool_summary()
        render_dashboard(
            manager, failover, server, http_proxy,
            f"Cycle #{cycle} done. Pool: {pool['alive']} alive, "
            f"{pool['dead_retryable']} retryable, "
            f"{pool['blacklisted']} blacklisted"
        )


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
async def main():
    print()
    print("  +==========================================+")
    print("  |   [+] Proxy Redirector v2.0              |")
    print("  |        Network Edition                   |")
    print("  +==========================================+")
    print("  |  Smart pool + second chances             |")
    print("  |  SOCKS5 Auth + Network Access            |")
    print("  +==========================================+")
    print(flush=True)

    # 1. Load
    manager = ProxyManager()
    proxies = manager.load_proxies()
    if not proxies:
        logger.error(f"[ERROR] No proxies in {config.PROXIES_FILE}!")
        sys.exit(1)

    # 2. Detect real IP (for anonymity check)
    logger.info("[SETUP] Detecting your real IP...")
    real_ip = await detect_real_ip()
    if real_ip:
        config.REAL_IP = real_ip
        logger.info(f"[SETUP] Real IP: {real_ip} — proxies leaking this will be rejected")
    else:
        logger.warning("[SETUP] Could not detect real IP — anonymity check disabled")
        config.ANONYMITY_CHECK = False

    # 3. Fast initial search
    logger.info(
        f"[SEARCH] Finding {config.MIN_ALIVE_POOL} working proxies "
        f"(batch={config.BATCH_SIZE})..."
    )
    results = await find_alive_proxies(proxies, needed=config.MIN_ALIVE_POOL)
    manager.update_status(results)

    alive_count = len(manager.get_alive_proxies())
    if alive_count == 0:
        logger.warning("[WARN] No working proxy yet! Will keep searching...")
    else:
        logger.info(f"[OK] Found {alive_count} working proxies!")

    # 4. Failover
    failover = FailoverHandler(manager)
    await failover.initialize()

    # 5. Start SOCKS5 immediately
    server = Socks5Server(failover)
    await server.start()
    logger.info(f"[READY] SOCKS5 on {config.LOCAL_HOST}:{config.LOCAL_PORT}")

    # 5.5 Start HTTP Proxy (للهواتف)
    http_proxy = HttpProxyServer(failover)
    await http_proxy.start()
    logger.info(f"[READY] HTTP Proxy on {config.LOCAL_HOST}:{config.HTTP_PROXY_PORT}")

    # عرض معلومات الوصول من الشبكة
    try:
        local_ips = []
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in local_ips and ip != "127.0.0.1":
                local_ips.append(ip)
        if local_ips:
            logger.info(f"[NETWORK] Access from other devices:")
            for ip in local_ips:
                logger.info(f"  → SOCKS5 proxy: {ip}:{config.LOCAL_PORT}")
                logger.info(f"  → HTTP  proxy:  {ip}:{config.HTTP_PROXY_PORT} (للهواتف)")
            if config.AUTH_ENABLED:
                logger.info(f"  → Username: {config.AUTH_USERNAME}")
                logger.info(f"  → Password: {config.AUTH_PASSWORD}")
    except Exception:
        pass

    render_dashboard(manager, failover, server, http_proxy, "Server started!")

    # 6. Background maintenance
    try:
        await maintain_pool(manager, failover, server, http_proxy)
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()
        await http_proxy.stop()
        logger.info("[EXIT] Done")


if __name__ == "__main__":
    import sys
    import os
    
    # ── إخفاء سطر الأوامر (Console) على ويندوز ──
    if os.name == 'nt' and getattr(config, 'HIDE_CONSOLE', False):
        try:
            import ctypes
            # إخفاء نافذة الكونسل (0 = SW_HIDE)
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except Exception:
            pass

    # ── منطق التشغيل (GUI أو Console) ──
    use_gui = getattr(config, 'START_WITH_GUI', False)
    if "--gui" in sys.argv or getattr(sys, 'frozen', False):
        use_gui = True
    if "--no-gui" in sys.argv:
        use_gui = False

    if use_gui:
        from gui.launcher import launch
        launch()
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n  [EXIT] Stopped by user\n")
