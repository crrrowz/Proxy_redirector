# 🔀 Proxy Redirector

> A smart, self-healing proxy management system with ad blocking, automatic failover, and a sleek desktop GUI dashboard.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Platform Windows](https://img.shields.io/badge/platform-Windows-lightgrey)

## ✨ Features

### Proxy Engine
- 🔄 **Smart Pool Management** — Automatically discovers, validates, and ranks proxies by speed, reliability, and recency
- ⚡ **Automatic Failover** — Seamlessly switches to the next best proxy when the active one fails
- 🌍 **Geographical Targeting** — Restrict proxy scanning and usage to a specific country
- ⏱️ **Speed Thresholds** — Define strict maximum response times to instantly reject slow proxies
- 🕵️ **Anonymity Check** — Rejects transparent proxies that leak your real IP

### 📈 Analytics Engine
- **Historical Tracking** — Permanent memory forming profiles for every checked proxy
- **Core Metrics** — Tracks lifetime uptime %, true average speed, and daily/hourly performance trends
- **Reliability Score** — 0-100 metric combining stability (40%), speed (30%), consistency (20%), and recency (10%)
- **Auto-Tagging** — Proxies automatically labeled as `fast`, `stable`, `slow`, or `unreliable`

### Network Servers
- 🔌 **SOCKS5 Server** — Local tunnel on `0.0.0.0:1080` for desktop apps
- 🌐 **HTTP Proxy** — Local proxy on `0.0.0.0:8080` for phones and browsers
- 🔐 **Authentication** — Username/password auth with whitelist for local network devices

### Ad Blocker
- 🛡️ **Built-in Ad & Tracker Blocker** — Blocks ads, trackers, and malware domains at the proxy level
- 📋 **50+ Default Rules** — Ships with a curated blocklist of common ad/tracking domains
- 🏷️ **Categories** — Ads, Tracking, Malware, Custom — each toggleable independently
- ✅ **Whitelist** — Exception domains that bypass blocking
- 📊 **Block Statistics** — Track total blocked, top blocked domains, per-category counts

### Dashboard GUI
- 🖥️ **Desktop App** — Native window via pywebview (frameless, modern dark theme)
- ⚙️ **Dynamic Settings** — Manage server ports, auth options, and engine rules straight from the GUI without editing code
- 📊 **Real-time Dashboard** — Live stat cards, proxy pool status, connected clients
- 📈 **Analytics Tab** — Leaderboard of best performing proxies globally and per country
- 📝 **Traffic Log** — Full request history with search, filter by status (success/blocked/failed)
- 🛡️ **Ad Blocker Management** — Add/remove rules, toggle categories, manage whitelist from the GUI

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Windows 10/11

### Setup

```bash
# Clone the repository
git clone https://github.com/crrrowz/Proxy_redirector.git
cd Proxy_redirector

# Install dependencies
pip install -r requirements.txt
```

### Prepare Your Proxies

Place your proxy list in `data/data.json`:

```json
[
  {
    "ip": "103.152.112.186",
    "port": 8080,
    "type": "socks5",
    "username": null,
    "password": null
  }
]
```

**Supported types:** `socks5`, `socks4`, `http`, `https`

---

## 🚀 Usage

### Application Modes

By default, the app can start GUI automatically and hide the console based on settings in the dashboard.
```bash
python main.py
```

Force GUI to open (if not set in settings):
```bash
python main.py --gui
```

Force Console only (headless mode):
```bash
python main.py --no-gui
```

### Connect Your Devices

| Device | Protocol | Address | Port |
|--------|----------|---------|------|
| Desktop Apps | SOCKS5 | `YOUR_IP` | `1080` |
| Phones / Browsers | HTTP Proxy | `YOUR_IP` | `8080` |

If authentication is enabled (default):
- **Username:** `admin`
- **Password:** `proxy2026`

### Quick Test
```bash
curl --socks5 127.0.0.1:1080 http://httpbin.org/ip
```

---

## ⚙️ Configuration

Settings are dynamically loaded and saved in `data/config.json`. You can edit them entirely from the **Settings** tab in the GUI Dashboard.

| Category | Example Settings |
|---------|-------------|
| **Server** | Local Port, HTTP Proxy Port, Bind address |
| **Authentication** | Enable/Disable Auth, Username, Password |
| **App Display** | Start GUI Automatically, Hide Console (Windows) |
| **Proxy Pool** | Min Alive, Batch Size, Target Country |
| **Proxy Checking** | Timeout, Anonymity Check, Max Speed Threshold |

---

## 📁 Project Structure

```
Proxy_redirector/
├── main.py                 # Entry point (console + GUI)
├── config.py               # All configuration settings
├── requirements.txt        # Python dependencies
│
├── core/                   # Core proxy engine
│   ├── proxy_manager.py    # Proxy loading, scoring, sorting
│   ├── proxy_checker.py    # Async proxy validation
│   ├── failover_handler.py # Automatic proxy switching
│   └── adblock_manager.py  # Ad/tracker blocking engine
│
├── servers/                # Network servers
│   ├── socks5_server.py    # SOCKS5 local tunnel
│   ├── http_proxy_server.py# HTTP proxy for phones
│   └── api_server.py       # REST API for dashboard
│
├── gui/                    # Desktop GUI
│   └── launcher.py         # pywebview window launcher
│
├── utils/                  # Utilities
│   └── traffic_logger.py   # Request logging & stats
│
├── data/                   # Data files 
│   ├── config.json         # Dynamic user settings
│   ├── data.json           # Your proxy list
│   ├── analytics.json      # Proxy historical performance memory
│   ├── proxies_status.json # Temporary proxy health status
│   └── blocklist.json      # Ad blocker rules
│
└── static/                 # Web dashboard UI
    ├── index.html
    ├── css/style.css
    └── js/app.js
```

---

## 📊 Scoring Algorithm

Each proxy receives a score based on:

| Factor | Weight |
|--------|--------|
| Currently alive | +50 |
| Response speed | 0 to +25 |
| Recency of last success | 0 to +15 |
| Overall success rate | 0 to +10 |
| Consecutive failures | -5 per failure |

The highest-scoring proxy is used first.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
