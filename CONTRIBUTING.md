# Contributing to Proxy Redirector

Thank you for your interest in contributing! 🎉

## Getting Started

### Prerequisites
- Python 3.10+
- Git
- Windows 10/11

### Setup Development Environment

```bash
# Fork and clone the repo
git clone https://github.com/crrrowz/Proxy_redirector.git
cd Proxy_redirector

# Create a virtual environment
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Console mode (headless)
python main.py --no-gui

# GUI mode
python main.py --gui

# Default (uses config settings in data/config.json)
python main.py
```

---

## Architecture Overview

### Data Flow

```
User Device (Phone/PC)
    │
    ├── SOCKS5 (:1080) ──→ Socks5Server
    │                          │
    └── HTTP   (:8080) ──→ HttpProxyServer
                               │
                     ┌─────────┴──────────┐
                     │  AdBlockManager     │  ← Check if blocked
                     │  (is_blocked())     │
                     └─────────┬──────────┘
                               │
                     ┌─────────┴──────────┐
                     │  FailoverHandler    │  ← Get active proxy
                     │  (get_active_proxy) │
                     └─────────┬──────────┘
                               │
                     ┌─────────┴──────────┐
                     │  ProxyManager       │  ← Sorted proxy list
                     │  (get_alive_proxies)│
                     └─────────┬──────────┘
                               │
                          Upstream Proxy ──→ Internet
```

### Module Responsibilities

| Module | File | Responsibility |
|--------|------|----------------|
| **ProxyManager** | `core/proxy_manager.py` | Load proxies from JSON, score & sort, track status, country filtering, second chance system |
| **ProxyChecker** | `core/proxy_checker.py` | Async proxy validation in batches, anonymity check, speed threshold enforcement |
| **FailoverHandler** | `core/failover_handler.py` | Track active proxy, suggest switches on failure, refresh best after check cycles |
| **AdBlockManager** | `core/adblock_manager.py` | Domain blocking (exact + wildcard), categories, whitelist, statistics |
| **ProxyAnalytics** | `core/proxy_analytics.py` | Historical performance tracking, reliability scoring, auto-tagging |
| **Socks5Server** | `servers/socks5_server.py` | SOCKS5 protocol implementation with auth (RFC 1929), ad blocking, relay |
| **HttpProxyServer** | `servers/http_proxy_server.py` | HTTP CONNECT tunnels, HTTP forwarding, WebSocket support, Basic Auth |
| **APIServer** | `servers/api_server.py` | REST API + ProxyEngine orchestrator, static file serving, async bridge |
| **TrafficLogger** | `utils/traffic_logger.py` | Request logging, per-client statistics, in-memory ring buffer |
| **Config** | `config.py` | JSON-backed dynamic config with runtime updates |
| **Launcher** | `gui/launcher.py` | pywebview window with loading screen, single-instance mutex |

### Key Design Patterns

- **Singleton:** `AdBlockManager`, `TrafficLogger`, `ProxyAnalytics` — all use `.get_instance()`
- **Non-destructive failover:** Servers never "kill" proxies — only `ProxyChecker` determines health status
- **Async/Threading bridge:** `ProxyEngine` runs async loop in a daemon thread; `APIHandler` uses `run_coroutine_threadsafe()` to bridge sync HTTP handler → async engine
- **Smart retry:** Dead proxies get retried after `DEAD_RETRY_AFTER_SECONDS`, sorted by least failures first

---

## Code Style

- **Language:** Python 3.10+ with type hints
- **Formatting:** 4-space indentation, max line length 100
- **Async:** All network operations use `asyncio`
- **Comments:** Arabic and English are both welcome
- **Logging:** Use the `logging` module, not `print()`
- **Singletons:** Use `get_instance()` classmethod pattern

## Project Layout

| Directory | Purpose |
|-----------|---------|
| `core/` | Core proxy engine (manager, checker, failover, adblock, analytics) |
| `servers/` | Network servers (SOCKS5, HTTP proxy, REST API + ProxyEngine) |
| `gui/` | Desktop GUI launcher (pywebview, single-instance) |
| `utils/` | Utility modules (traffic logger) |
| `data/` | Data files (proxies, status, config, blocklist, analytics) |
| `static/` | Web dashboard (HTML, CSS, JS) — served by API server |

## Making Changes

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/my-change`)
3. Make your changes
4. **Test** locally (both console and GUI modes)
5. **Commit** with a clear message
6. **Push** and open a Pull Request

### Testing Checklist

- [ ] Console mode works (`python main.py --no-gui`)
- [ ] GUI mode works (`python main.py --gui`)
- [ ] SOCKS5 proxy accepts connections on configured port
- [ ] HTTP proxy accepts connections on configured port
- [ ] Ad blocker correctly blocks domains in blocklist
- [ ] Settings changes persist in `data/config.json`
- [ ] No regressions in existing API endpoints

## Reporting Issues

When reporting a bug, please include:
- Python version (`python --version`)
- Operating system and version
- Steps to reproduce
- Expected vs actual behavior
- Error logs (if any)
- Contents of `data/config.json` (if relevant)

## Questions?

Open a [Discussion](https://github.com/crrrowz/Proxy_redirector/discussions) or an [Issue](https://github.com/crrrowz/Proxy_redirector/issues).
