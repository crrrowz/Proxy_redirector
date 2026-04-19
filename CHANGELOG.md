# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] — 2026-04-19

### Added
- 📈 **Proxy Analytics Engine** — Permanent tracking of uptime %, average speed, and daily trends.
  - Proxy Auto-Tagging (`fast`, `stable`, `slow`, `unreliable`).
  - Reliability Leaderboard for the best global proxies.
  - Country Performance tracking.
- 🌍 **Geographical Targeting** — Only scan and use proxies from a specific chosen country.
- ⏱️ **Speed Threshold Control** — Automatically reject proxies strictly slower than a given time limit.
- ⚙️ **Dynamic Settings UI** — Manage server ports, authentication, pool behavior, and engine rules from the new `Settings` GUI tab without editing code.
- 🖥️ **App Display Settings** — Easily configure the app to `Start GUI Automatically` and `Hide Console (Windows)` entirely from the new UI.

## [2.1.0] — 2026-04-19

### Added
- 🛡️ **Ad Blocker Engine** — Built-in ad, tracker, and malware domain blocking
  - 50+ default block rules for common ad networks and trackers
  - Category system (Ads, Tracking, Malware, Custom) with independent toggles
  - Whitelist/exceptions for domains that should bypass blocking
  - Block statistics with top blocked domains tracking
  - Persistent rules in `data/blocklist.json`
- 📊 **Dashboard Redesign** — Complete UI overhaul
  - Sidebar navigation with 4 tabs (Dashboard, Proxy Pool, Ad Blocker, Traffic Log)
  - Stat cards with gradient accents and live counters
  - Search and filter on proxy pool and traffic log tables
  - Traffic status filter (All / Success / Blocked / Failed)
  - Blocked requests highlighted with 🚫 icon
- 📁 **Project Restructuring** — Organized codebase
  - `core/` — Proxy engine modules
  - `servers/` — Network server modules
  - `gui/` — Desktop GUI launcher
  - `utils/` — Utility modules
  - `data/` — Data files
- 📝 **GitHub Documentation**
  - Professional README with full feature list and setup guide
  - CONTRIBUTING.md with development guidelines
  - MIT License
  - .gitignore for Python projects
  - This CHANGELOG

## [2.0.0] — 2026-04-18

### Added
- 🖥️ **Desktop GUI Dashboard** — pywebview-based desktop application
- 🌐 **HTTP Proxy Server** — For phones and browsers that don't support SOCKS5
- 🔐 **Authentication** — Username/password with local network whitelist
- 📝 **Traffic Logger** — Request tracking with client statistics
- 🔌 **REST API** — Internal API server bridging GUI to proxy engine
- 👥 **Multi-client Support** — Network-wide access from any device

## [1.0.0] — 2026-04-16

### Added
- 🔄 **Proxy Pool Management** — Load, validate, and rank proxies from JSON
- ⚡ **Smart Scoring** — Speed, reliability, and recency-based ranking
- 🔁 **Failover** — Automatic switching on proxy failure
- 🔌 **SOCKS5 Server** — Local tunnel for desktop applications
- 📊 **Console Dashboard** — Real-time status display in terminal
- 🔁 **Second Chance System** — Dead proxies retried after cooldown period
