# Contributing to Proxy Redirector

Thank you for your interest in contributing! 🎉

## Getting Started

### Prerequisites
- Python 3.10+
- Git

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
# Console mode
python main.py

# GUI mode
python main.py --gui
```

## Code Style

- **Language:** Python 3.10+ with type hints
- **Formatting:** 4-space indentation, max line length 100
- **Async:** All network operations use `asyncio`
- **Comments:** Arabic and English are both welcome
- **Logging:** Use the `logging` module, not `print()`

## Project Layout

| Directory | Purpose |
|-----------|---------|
| `core/` | Core proxy engine (manager, checker, failover, adblock) |
| `servers/` | Network servers (SOCKS5, HTTP proxy, REST API) |
| `gui/` | Desktop GUI launcher (pywebview) |
| `utils/` | Utility modules (traffic logger) |
| `data/` | Data files (proxies, status, blocklist) |
| `static/` | Web dashboard (HTML, CSS, JS) |

## Making Changes

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/my-change`)
3. Make your changes
4. **Test** locally (both console and GUI modes)
5. **Commit** with a clear message
6. **Push** and open a Pull Request

## Reporting Issues

When reporting a bug, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error logs (if any)

## Questions?

Open a [Discussion](https://github.com/crrrowz/Proxy_redirector/discussions) or an [Issue](https://github.com/crrrowz/Proxy_redirector/issues).
