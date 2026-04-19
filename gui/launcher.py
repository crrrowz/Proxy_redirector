"""
Proxy Redirector — GUI Launcher
نافذة سطح مكتب باستخدام pywebview.
تعرض صفحة تحميل فورياً ثم تنتقل للواجهة عند جهوزية السيرفر.
"""

import os
import sys
import time
import threading
import traceback
import urllib.request

_URL = f"http://127.0.0.1:9090/?_ts={int(time.time())}"
_MUTEX_NAME = "Global\\ProxyRedirector_SingleInstance"
_mutex_handle = None


def _acquire_single_instance_lock() -> bool:
    """منع تشغيل أكثر من نسخة."""
    global _mutex_handle
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        ERROR_ALREADY_EXISTS = 183
        _mutex_handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None
            return False
        return True
    except Exception:
        return True


def _focus_existing_window():
    """إظهار النافذة الموجودة."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Proxy Redirector")
        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def _wait_for_server(url: str, timeout: float = 15.0) -> bool:
    """انتظار السيرفر حتى يجيب."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def _run_server():
    """تشغيل API server في خلفية."""
    try:
        from servers.api_server import start_api_server
        start_api_server()
    except Exception:
        print(f"[SERVER CRASH] {traceback.format_exc()}")


def launch():
    """تشغيل الواجهة الرسومية."""
    try:
        # حماية من النسخ المتعددة
        if not _acquire_single_instance_lock():
            _focus_existing_window()
            sys.exit(0)

        import webview
        from pathlib import Path

        # مسار ملفات static
        if getattr(sys, 'frozen', False):
            _base = Path(sys._MEIPASS) / 'static'
        else:
            _base = Path(__file__).parent.parent / 'static'

        loading_url = (_base / 'loading.html').as_uri()

        # إنشاء النافذة فوراً مع صفحة التحميل
        window = webview.create_window(
            title="Proxy Redirector",
            url=loading_url,
            width=1150,
            height=750,
            min_size=(900, 600),
            resizable=True,
            frameless=True,
            background_color='#0a0e17',
        )

        class WindowAPI:
            """تُكشف لـ JS عبر pywebview.api.*"""
            def __init__(self, win):
                self._win = win

            def minimize(self):
                self._win.minimize()

            def toggle_maximize(self):
                self._win.toggle_fullscreen()

            def close(self):
                from servers.api_server import stop_api_server
                stop_api_server()
                self._win.destroy()

        api = WindowAPI(window)
        window.expose(api.minimize, api.toggle_maximize, api.close)

        def _boot_server_then_navigate():
            """تشغيل السيرفر ثم الانتقال للواجهة."""
            server_thread = threading.Thread(target=_run_server, daemon=True)
            server_thread.start()

            ready = _wait_for_server(_URL)
            if ready:
                window.load_url(_URL)
            else:
                print("[ERROR] Server did not start within 15s")

        webview.start(func=_boot_server_then_navigate)
        os._exit(0)

    except Exception:
        print(f"[LAUNCH CRASH] {traceback.format_exc()}")
        os._exit(1)


if __name__ == "__main__":
    launch()
