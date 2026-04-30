# 🔀 Proxy Redirector

> نظام إدارة بروكسي ذكي وذاتي الإصلاح مع حجب إعلانات مدمج، تبديل تلقائي عند الفشل، ولوحة تحكم رسومية أنيقة.
>
> A smart, self-healing proxy management system with ad blocking, automatic failover, and a sleek desktop GUI dashboard.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Platform Windows](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## ✨ Features

### Proxy Engine
- 🔄 **Smart Pool Management** — Automatically discovers, validates, and ranks proxies by speed, reliability, and recency
- ⚡ **Automatic Failover** — Seamlessly switches to the next best proxy when the active one fails
- 🌍 **Geographical Targeting** — Restrict proxy scanning and usage to a specific country (ISO code filter)
- ⏱️ **Speed Thresholds** — Define strict maximum response times to instantly reject slow proxies
- 🕵️ **Anonymity Check** — Rejects transparent proxies that leak your real IP
- 🔁 **Second Chance System** — Dead proxies are retried after a cooldown period before being permanently blacklisted

### 📈 Analytics Engine
- **Historical Tracking** — Permanent memory forming profiles for every checked proxy (saved in `data/analytics.json`)
- **Core Metrics** — Tracks lifetime uptime %, true average speed, min/max speed, and daily/hourly performance trends
- **Reliability Score** — 0-100 metric combining stability (40%), speed (30%), consistency (20%), and recency (10%)
- **Auto-Tagging** — Proxies automatically labeled as `fast`, `stable`, `slow`, `unreliable`, `new`, or `recommended`
- **Country Performance** — Aggregate statistics per country (avg speed, uptime, reliability)

### Network Servers
- 🔌 **SOCKS5 Server** — Local tunnel on `0.0.0.0:1080` for desktop apps and advanced phone apps
- 🌐 **HTTP Proxy** — Local proxy on `0.0.0.0:8080` for phones and browsers
- 🔐 **Authentication** — Username/password auth with automatic whitelist for local network devices (`192.168.x.x`, `127.0.0.1`)
- 🌐 **REST API** — Internal API server on `127.0.0.1:9090` bridging GUI to proxy engine

### 🛡️ Ad & Tracker Blocker
- **Built-in Ad & Tracker Blocker** — Blocks ads, trackers, and malware domains at the proxy level (both SOCKS5 & HTTP)
- 📋 **50+ Default Rules** — Ships with a curated blocklist of common ad/tracking domains (Google Ads, Facebook Pixel, Criteo, Taboola, etc.)
- 🏷️ **Categories** — `ads`, `tracking`, `malware`, `custom` — each toggleable independently
- 🔤 **Wildcard Patterns** — Support for patterns like `*ads.*`, `*tracker.*`, `*adserver*`
- ✅ **Whitelist** — Exception domains that bypass blocking
- 📊 **Block Statistics** — Track total blocked, top blocked domains, per-category counts

### Dashboard GUI
- 🖥️ **Desktop App** — Native window via pywebview (frameless, modern dark theme, `#0a0e17` background)
- 🚀 **Instant Launch** — Loading screen shown immediately, servers start in background, UI loads when ready
- ⚙️ **Dynamic Settings** — Manage server ports, auth options, pool behavior, and engine rules from the Settings tab
- 📊 **Real-time Dashboard** — Live stat cards, proxy pool status, connected clients
- 📈 **Analytics Tab** — Leaderboard of best performing proxies globally and per country
- 📝 **Traffic Log** — Full request history with search, filter by status (success/blocked/failed)
- 🛡️ **Ad Blocker Management** — Add/remove rules, toggle categories, manage whitelist from the GUI
- 🔒 **Single Instance** — Windows Mutex prevents multiple instances from running simultaneously

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

### Dependencies
| Package | Purpose |
|---------|---------|
| `aiohttp>=3.9.0` | Async HTTP client for proxy checking |
| `aiohttp-socks>=0.8.0` | SOCKS proxy connector for aiohttp |
| `python-socks[asyncio]>=2.4.0` | SOCKS4/5 proxy connections |
| `pywebview>=5.0` | Desktop GUI window |

### Prepare Your Proxies

Place your proxy list in `data/data.json`. Supports two formats:

**Format 1 — Array of proxies:**
```json
[
  {
    "ip": "103.152.112.186",
    "port": 8080,
    "type": "socks5",
    "username": null,
    "password": null,
    "geolocation": {
      "country": "US",
      "city": "New York"
    }
  }
]
```

**Format 2 — Object with proxies key:**
```json
{
  "proxies": [
    {
      "ip": "103.152.112.186",
      "port": 8080,
      "type": "socks5"
    }
  ]
}
```

**Supported types:** `socks5`, `socks4`, `http`, `https`

> **Note:** `http` type is internally treated as `https`. The `geolocation` field is optional but enables country filtering.

---

## 🚀 Usage

### Application Modes

By default, the app starts the GUI automatically and hides the console based on settings in `data/config.json`.

```bash
# Default (uses config settings)
python main.py

# Force GUI mode
python main.py --gui

# Force Console-only (headless)
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

> **Note:** Devices on the local network (`192.168.x.x`, `127.0.0.1`) are automatically whitelisted and don't need authentication.

### Quick Test
```bash
# Test SOCKS5
curl --socks5 127.0.0.1:1080 http://httpbin.org/ip

# Test HTTP Proxy
curl --proxy http://admin:proxy2026@127.0.0.1:8080 http://httpbin.org/ip
```

---

## 🖥️ PC Setup Guide — إعداد الكمبيوتر

يمكنك استخدام البروكسي على الكمبيوتر بطريقتين: عبر إعدادات النظام (Windows) أو عبر تطبيق **Proxifier**.

### الطريقة 1: إعدادات نظام ويندوز (HTTP Proxy)

هذه الطريقة تُمرر حركة المتصفحات والتطبيقات التي تدعم بروكسي النظام.

#### Windows 10 / 11

1. افتح **الإعدادات** (Settings) → اضغط `Win + I`
2. اذهب إلى **الشبكة والإنترنت** (Network & Internet)
3. اضغط على **الخادم الوكيل** (Proxy)
4. في قسم **إعداد الوكيل يدوياً** (Manual proxy setup) اضغط **إعداد** (Set up) أو فعّل **استخدام خادم وكيل** (Use a proxy server)
5. أدخل البيانات:
   - **العنوان** (Address): `127.0.0.1`
   - **المنفذ** (Port): `8080`
6. اضغط **حفظ** (Save)

> 💡 **ملاحظة:** إعدادات البروكسي في ويندوز تعمل مع المتصفحات (Chrome, Edge) والتطبيقات التي تستخدم إعدادات نظام البروكسي. بعض التطبيقات مثل الألعاب أو برامج التورنت **لا تدعم** بروكسي النظام.

#### إعداد البروكسي عبر سطر الأوامر (CMD/PowerShell)

```powershell
# تفعيل البروكسي
netsh winhttp set proxy 127.0.0.1:8080

# إلغاء البروكسي
netsh winhttp reset proxy
```

#### إعداد البروكسي لمتصفح Firefox فقط

Firefox يستخدم إعداداته الخاصة بدلاً من إعدادات النظام:

1. افتح Firefox → **الإعدادات** (Settings)
2. مرر للأسفل حتى **إعدادات الشبكة** (Network Settings) → اضغط **الإعدادات** (Settings)
3. اختر **إعداد يدوي للخادم الوكيل** (Manual proxy configuration)
4. أدخل:
   - **HTTP Proxy**: `127.0.0.1` — **Port**: `8080`
   - ✅ فعّل **استخدام هذا الخادم الوكيل لجميع البروتوكولات** (Also use this proxy for HTTPS)
5. اضغط **موافق** (OK)

#### 🔄 إيقاف البروكسي

- ارجع إلى **إعدادات الخادم الوكيل** وأوقف **استخدام خادم وكيل** (Use a proxy server)
- أو من CMD: `netsh winhttp reset proxy`

---

### الطريقة 2: تطبيق Proxifier (SOCKS5) — جميع التطبيقات

**Proxifier** هو تطبيق احترافي يُمرر حركة **جميع التطبيقات** على الكمبيوتر عبر البروكسي، بما في ذلك التطبيقات التي لا تدعم إعدادات البروكسي (الألعاب، برامج التورنت، تطبيقات الدردشة، إلخ).

#### 📥 التثبيت

1. حمّل **Proxifier** من الموقع الرسمي: [https://www.proxifier.com/download/](https://www.proxifier.com/download/)
2. ثبّت البرنامج وشغّله

#### ⚙️ إعداد سيرفر البروكسي

1. افتح **Proxifier**
2. اذهب إلى **Profile** → **Proxy Servers** (أو اضغط `Alt+P`)
3. اضغط **Add**
4. أدخل البيانات:
   - **Address**: `127.0.0.1`
   - **Port**: `1080`
   - **Protocol**: اختر **SOCKS Version 5**
   - **Authentication**: فعّلها إذا كانت المصادقة مطلوبة
     - **Username**: `admin`
     - **Password**: `proxy2026`
5. اضغط **Check** للتأكد من عمل البروكسي
6. اضغط **OK**

#### 📋 إعداد قواعد التوجيه (Proxification Rules)

بشكل افتراضي، Proxifier يُمرر كل التطبيقات عبر البروكسي. يمكنك تخصيص ذلك:

1. اذهب إلى **Profile** → **Proxification Rules** (أو اضغط `Alt+R`)
2. يمكنك إنشاء قواعد مخصصة مثل:
   - **تمرير تطبيقات محددة فقط:** أضف قاعدة جديدة → حدد التطبيق (مثل `chrome.exe`) → Action: `Proxy SOCKS5`
   - **استثناء تطبيقات:** أضف قاعدة → حدد التطبيق → Action: `Direct` (اتصال مباشر بدون بروكسي)
   - **حظر تطبيق:** Action: `Block`

#### 🛡️ إعداد DNS عبر البروكسي

لمنع تسريب DNS:

1. اذهب إلى **Profile** → **Name Resolution**
2. اختر **Resolve hostnames through proxy** (حل أسماء المضيف عبر البروكسي)
3. اضغط **OK**

#### ⚠️ ملاحظات مهمة حول Proxifier

- Proxifier هو برنامج مدفوع ولكن يوفر فترة تجريبية مجانية (31 يوم)
- يعمل على مستوى النظام — يمكنه تمرير أي تطبيق حتى لو لا يدعم البروكسي
- يعرض لوحة تحكم تُظهر كل الاتصالات الجارية في الوقت الحقيقي
- تأكد أن **Proxy Redirector** يعمل قبل تشغيل Proxifier
- لا تُمرر البرنامج نفسه (Proxifier) أو بروكسي ريداريكتور عبر البروكسي (يُستثنى تلقائياً)

#### 🔄 إيقاف Proxifier

- اضغط على زر **الإيقاف** (■) في شريط أدوات Proxifier
- أو أغلق البرنامج بالكامل

---

### مقارنة بين طريقتي الكمبيوتر

| | إعدادات النظام (HTTP) | Proxifier (SOCKS5) |
|---|---|---|
| **السعر** | مجاني | مدفوع (تجريبي 31 يوم) |
| **التغطية** | المتصفحات + بعض التطبيقات | جميع التطبيقات |
| **البروتوكول** | HTTP Proxy (منفذ `8080`) | SOCKS5 (منفذ `1080`) |
| **حجب الإعلانات** | ✅ نعم | ✅ نعم |
| **حماية DNS** | ❌ لا | ✅ نعم |
| **قواعد مخصصة** | ❌ لا | ✅ نعم (لكل تطبيق) |
| **سهولة الإعداد** | ⭐⭐⭐ سهل جداً | ⭐⭐ متوسط |

**التوصية:**
- لتصفح الإنترنت فقط → **إعدادات النظام** (مجاني وسريع)
- لتغطية كل التطبيقات (ألعاب، تورنت، دردشة) → **Proxifier**

---

## 📱 Mobile Setup Guide — إعداد الهاتف

يمكنك استخدام البروكسي على هاتفك بطريقتين: عبر إعدادات النظام مباشرة أو عبر تطبيق **SocksDroid**.

> **ملاحظة مهمة:** يجب أن يكون الهاتف قادراً على الوصول إلى عنوان IP الكمبيوتر (انظر شرح الشبكات أدناه).

### الخطوة 0: معرفة عنوان IP الكمبيوتر

1. على الكمبيوتر، افتح **Command Prompt** (موجه الأوامر)
2. اكتب: `ipconfig`
3. ابحث عن **IPv4 Address** تحت محول الشبكة (Ethernet أو WiFi)
4. هذا هو العنوان الذي ستستخدمه في الهاتف

> بديل: عند تشغيل البرنامج، يعرض في الكونسل عناوين IP المحلية تحت `[NETWORK] Access from other devices`.

### 🌐 فهم بنية الشبكة — هل يمكن للهاتف الوصول للكمبيوتر؟

#### الحالة 1: الكمبيوتر والهاتف على نفس الشبكة (الأسهل ✅)

إذا كان الكمبيوتر والهاتف متصلين بنفس الراوتر (سواء عبر Ethernet أو WiFi):

```
📡 الراوتر (192.168.1.1)
    ├── 🖥️ الكمبيوتر (Ethernet) → 192.168.1.100
    └── 📱 الهاتف (WiFi)        → 192.168.1.50
```

في هذه الحالة، الهاتف يستخدم عنوان الكمبيوتر مباشرة: `192.168.1.100`

#### الحالة 2: الكمبيوتر على مودم مختلف عن الراوتر (شبكتين مختلفتين) ✅

هذا سيناريو شائع: الكمبيوتر متصل مباشرة بمودم مزود الإنترنت عبر Ethernet، والهاتف متصل براوتر WiFi آخر مربوط بنفس المودم:

```
🌐 مودم الإنترنت (ISP Modem / Gateway)
    │
    ├── 🖥️ الكمبيوتر (Ethernet مباشر) → 192.168.100.2
    │
    └── 📡 الراوتر (WiFi Router)       → 192.168.100.1 (WAN)
             │                            192.168.0.1   (LAN)
             └── 📱 الهاتف (WiFi)      → 192.168.0.2
```

**هل يعمل؟ نعم! ✅** ولكن بشرط:

1. **المودم يسمح بالتوجيه بين الشبكتين** — معظم مودمات مزودي الإنترنت تفعل ذلك تلقائياً
2. **جدار الحماية** على الكمبيوتر يسمح بالاتصالات الواردة على المنافذ `1080` و `8080`

**في هذه الحالة:**
- الهاتف يستخدم عنوان الكمبيوتر كما يراه المودم: `192.168.100.2`
- المنفذ: `8080` (HTTP) أو `1080` (SOCKS5 عبر SocksDroid)

**المصادقة:** البرنامج يأتي بقائمة بيضاء تلقائية تشمل `192.168.100.*` و `192.168.0.*` و `192.168.1.*` — يعني **الهاتف لن يحتاج إلى اسم مستخدم وكلمة مرور** لأنه مُعرّف تلقائياً كجهاز محلي.

#### إذا لم يعمل الاتصال — خطوات التشخيص:

1. **اختبر الوصول:** من الهاتف، افتح المتصفح واكتب `http://192.168.100.2:9090` — إذا ظهرت لوحة التحكم فالاتصال يعمل
2. **جدار حماية ويندوز:** قد يحظر الاتصالات. افتح **Windows Defender Firewall** وأضف قاعدة تسمح بالمنافذ `1080`, `8080`, `9090`
   ```powershell
   # فتح المنافذ في جدار الحماية (تشغيل كمسؤول)
   netsh advfirewall firewall add rule name="Proxy Redirector" dir=in action=allow protocol=TCP localport=1080,8080,9090
   ```
3. **إعدادات الراوتر:** بعض الراوترات تعزل الأجهزة (AP Isolation) — تأكد أنها معطلة
4. **إضافة شبكة فرعية للقائمة البيضاء:** إذا كانت شبكتك مختلفة، أضفها في الإعدادات:
   ```json
   "AUTH_WHITELIST": ["192.168.100.", "192.168.0.", "192.168.1.", "10.0.0.", "127.0.0.1"]
   ```

---

### الطريقة 1: إعدادات النظام (HTTP Proxy) — لجميع الهواتف

هذه الطريقة تعمل على **أندرويد** و **آيفون** بدون تثبيت أي تطبيق. تُمرر كل اتصالات WiFi عبر البروكسي.

#### 📱 أندرويد (Android)

1. افتح **الإعدادات** (Settings)
2. اذهب إلى **الشبكة والإنترنت** (Network & Internet) → **WiFi**
3. اضغط مطولاً على شبكة WiFi المتصل بها → اختر **تعديل الشبكة** (Modify Network)
   - أو: اضغط على أيقونة ⚙️ بجانب اسم الشبكة
4. اضغط على **خيارات متقدمة** (Advanced Options)
5. في قسم **البروكسي** (Proxy) اختر **يدوي** (Manual)
6. أدخل البيانات:
   - **اسم المضيف** (Proxy hostname): `192.168.1.100` ← عنوان IP الكمبيوتر
   - **المنفذ** (Proxy port): `8080`
7. اضغط **حفظ** (Save)

**إذا كانت المصادقة مطلوبة** (أول طلب في المتصفح سيطلب اسم مستخدم وكلمة مرور):
- **اسم المستخدم:** `admin`
- **كلمة المرور:** `proxy2026`

> ⚠️ **تنبيه:** إعدادات البروكسي في أندرويد تعمل فقط مع اتصال WiFi وليس بيانات الهاتف. كما أن بعض التطبيقات قد تتجاهل إعدادات البروكسي للنظام.

#### 🍎 آيفون (iOS)

1. افتح **الإعدادات** (Settings)
2. اذهب إلى **WiFi**
3. اضغط على أيقونة **ⓘ** بجانب اسم شبكة WiFi المتصل بها
4. مرر للأسفل حتى قسم **HTTP Proxy**
5. اختر **يدوي** (Manual)
6. أدخل البيانات:
   - **الخادم** (Server): `192.168.1.100` ← عنوان IP الكمبيوتر
   - **المنفذ** (Port): `8080`
   - **المصادقة** (Authentication): فعّلها إذا كانت المصادقة مطلوبة
   - **اسم المستخدم** (Username): `admin`
   - **كلمة المرور** (Password): `proxy2026`
7. ارجع للخلف — يتم الحفظ تلقائياً

#### ✅ اختبار عمل البروكسي

بعد الإعداد، افتح المتصفح على الهاتف واذهب إلى:
```
http://httpbin.org/ip
```
إذا ظهر عنوان IP مختلف عن عنوانك الحقيقي → البروكسي يعمل بنجاح! 🎉

#### 🔄 إيقاف البروكسي

لإيقاف استخدام البروكسي، ارجع لنفس الإعدادات وغيّر البروكسي من **يدوي** إلى **بلا** (None) أو **تلقائي** (Auto).

---

### الطريقة 2: تطبيق SocksDroid (SOCKS5) — أندرويد فقط

تطبيق **SocksDroid** يسمح بتوجيه كل حركة الهاتف عبر بروكسي SOCKS5 باستخدام VPN داخلي، مما يشمل **جميع التطبيقات** وليس فقط المتصفح.

#### 📥 التثبيت

1. حمّل **SocksDroid** من [Google Play Store](https://play.google.com/store/apps/details?id=net.typeblog.socks)
   - أو ابحث عن `SocksDroid` في متجر Play
2. ثبّت التطبيق

#### ⚙️ الإعداد

1. افتح تطبيق **SocksDroid**
2. أدخل البيانات التالية:
   - **Server Address** (عنوان الخادم): `192.168.1.100` ← عنوان IP الكمبيوتر
   - **Server Port** (المنفذ): `1080`
   - **Username** (اسم المستخدم): `admin` — فقط إذا كانت المصادقة مفعلة
   - **Password** (كلمة المرور): `proxy2026` — فقط إذا كانت المصادقة مفعلة
3. فعّل خيار **DNS over SOCKS** (اختياري لكن يُنصح به لحماية أفضل)
4. اضغط زر **التشغيل** (▶) في أعلى الشاشة
5. سيظهر طلب إذن VPN — اضغط **موافق** (OK)

#### ⚠️ ملاحظات مهمة حول SocksDroid

- SocksDroid يعمل عبر إنشاء VPN محلي على الهاتف — **لا يُرسل بياناتك لخادم خارجي**
- جميع التطبيقات على الهاتف ستمر عبر البروكسي (وليس المتصفح فقط)
- إذا أغلقت البرنامج على الكمبيوتر أو فقدت الاتصال، سيفقد الهاتف الاتصال بالإنترنت → أوقف SocksDroid لاستعادة الاتصال المباشر
- يمكنك استثناء تطبيقات معينة من إعدادات التطبيق (Per-App Proxy)
- تأكد أن البروكسي يعمل (**SOCKS5** على المنفذ `1080`) قبل تشغيل SocksDroid

#### 🔄 إيقاف SocksDroid

اضغط زر **الإيقاف** (⬛) في التطبيق أو أغلق الـ VPN من إشعارات الهاتف.

---

### مقارنة بين الطريقتين

| | إعدادات النظام (HTTP) | SocksDroid (SOCKS5) |
|---|---|---|
| **النظام** | أندرويد + آيفون | أندرويد فقط |
| **يحتاج تطبيق** | لا | نعم |
| **التغطية** | المتصفح + بعض التطبيقات | جميع التطبيقات |
| **البروتوكول** | HTTP Proxy (منفذ `8080`) | SOCKS5 (منفذ `1080`) |
| **حجب الإعلانات** | ✅ نعم | ✅ نعم |
| **حماية DNS** | ❌ لا | ✅ نعم (DNS over SOCKS) |
| **سهولة الإعداد** | ⭐⭐⭐ سهل جداً | ⭐⭐ متوسط |

**التوصية:**
- للاستخدام السريع على أي هاتف → **إعدادات النظام**
- لتغطية جميع التطبيقات مع حماية DNS على أندرويد → **SocksDroid**

---

## 🛡️ Ad & Site Blocking — حجب الإعلانات والمواقع

### كيف يعمل حجب الإعلانات؟

نظام الحجب يعمل على **مستوى البروكسي** — أي أن كل طلب اتصال يمر عبر البروكسي (سواء SOCKS5 أو HTTP) يتم فحصه قبل تمريره:

```
📱 الهاتف/المتصفح → طلب اتصال → 🔍 فحص AdBlock → ✅ مسموح → 🌐 الإنترنت
                                                    → 🚫 محظور → ❌ رفض الاتصال
```

### آلية الفحص (3 مراحل):

1. **القائمة البيضاء (Whitelist):** إذا كان الدومين في القائمة البيضاء ← مسموح دائماً (تتجاوز كل شيء)
2. **المطابقة الدقيقة (Exact Match):** فحص الدومين ضد قائمة الدومينات المحظورة (سرعة `O(1)`)
   - يفحص أيضاً الدومينات الأب (مثل: `ads.example.com` يُحظر إذا كان `example.com` محظوراً)
3. **الأنماط العامة (Wildcard):** مطابقة أنماط مثل `*ads.*` أو `*tracker.*`

### التصنيفات المدعومة

| التصنيف | الوصف | أمثلة |
|---------|-------|-------|
| `ads` | شبكات الإعلانات | `doubleclick.net`, `googlesyndication.com`, `taboola.com` |
| `tracking` | أدوات التتبع والتحليلات | `facebook.net`, `hotjar.com`, `clarity.ms` |
| `malware` | مواقع البرمجيات الخبيثة | `malwaredomainlist.com` |
| `custom` | قواعد مخصصة يضيفها المستخدم | أي دومين تريد حظره |

### إدارة قواعد الحجب

#### من واجهة GUI:
1. افتح تبويب **Ad Blocker** في لوحة التحكم
2. **إضافة قاعدة:** أدخل الدومين واختر التصنيف → اضغط Add
3. **حذف قاعدة:** اضغط على زر الحذف بجانب القاعدة
4. **تشغيل/إيقاف تصنيف:** استخدم مفاتيح التبديل لكل تصنيف
5. **القائمة البيضاء:** أضف دومينات مستثناة في قسم Whitelist

#### من REST API:
```bash
# إضافة قاعدة حظر
curl -X POST http://127.0.0.1:9090/api/blocklist/rules \
  -H "Content-Type: application/json" \
  -d '{"action":"add", "domain":"example-ads.com", "category":"ads"}'

# حذف قاعدة
curl -X POST http://127.0.0.1:9090/api/blocklist/rules \
  -H "Content-Type: application/json" \
  -d '{"action":"remove", "domain":"example-ads.com"}'

# إضافة استثناء (القائمة البيضاء)
curl -X POST http://127.0.0.1:9090/api/blocklist/whitelist \
  -H "Content-Type: application/json" \
  -d '{"action":"add", "domain":"safe-site.com"}'

# تشغيل/إيقاف تصنيف
curl -X POST http://127.0.0.1:9090/api/blocklist/toggle \
  -H "Content-Type: application/json" \
  -d '{"category":"ads", "enabled":false}'

# تشغيل/إيقاف المحرك بالكامل
curl -X POST http://127.0.0.1:9090/api/blocklist/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

### حجب مواقع مخصصة

يمكنك استخدام نظام الحجب لحظر **أي موقع** (ليس فقط الإعلانات):

```bash
# حظر موقع بالكامل
curl -X POST http://127.0.0.1:9090/api/blocklist/rules \
  -d '{"action":"add", "domain":"blocked-site.com", "category":"custom"}'

# حظر باستخدام نمط wildcard (كل الدومينات الفرعية)
curl -X POST http://127.0.0.1:9090/api/blocklist/rules \
  -d '{"action":"add", "domain":"*.blocked-site.com", "category":"custom"}'
```

> **ملاحظة:** الحجب يعمل على كل الأجهزة المتصلة بالبروكسي (الكمبيوتر والهاتف). هذا يجعله مفيداً لحجب المواقع غير المرغوبة على مستوى الشبكة.

### ملف قواعد الحجب

القواعد محفوظة في `data/blocklist.json` ويتم تحميلها تلقائياً عند التشغيل:

```json
{
  "enabled": true,
  "categories_enabled": {
    "ads": true,
    "tracking": true,
    "malware": true,
    "custom": true
  },
  "exact_domains": {
    "doubleclick.net": "ads",
    "facebook.net": "tracking"
  },
  "wildcard_rules": [
    {"pattern": "*ads.*", "category": "ads"}
  ],
  "whitelist": ["safe-site.com"]
}
```

---

## ⚙️ Configuration

Settings are dynamically loaded and saved in `data/config.json`. You can edit them entirely from the **Settings** tab in the GUI Dashboard or via the REST API.

| Category | Settings | Default |
|----------|----------|---------|
| **Server** | `LOCAL_PORT`, `HTTP_PROXY_PORT`, `LOCAL_HOST` | `1080`, `8080`, `0.0.0.0` |
| **Authentication** | `AUTH_ENABLED`, `AUTH_USERNAME`, `AUTH_PASSWORD`, `AUTH_WHITELIST` | `true`, `admin`, `proxy2026` |
| **App Display** | `START_WITH_GUI`, `HIDE_CONSOLE` | `true`, `true` |
| **Proxy Pool** | `MIN_ALIVE_POOL`, `BATCH_SIZE`, `RECHECK_INTERVAL_SECONDS` | `3`, `50`, `60s` |
| **Proxy Checking** | `CHECK_TIMEOUT_SECONDS`, `ANONYMITY_CHECK`, `MAX_SPEED_MS` | `8s`, `true`, `0` (no limit) |
| **Retry & Blacklist** | `DEAD_RETRY_AFTER_SECONDS`, `MAX_CONSECUTIVE_FAILURES`, `BLACKLIST_AFTER_FAILURES` | `300s`, `5`, `15` |
| **Country Filter** | `COUNTRY_FILTER` | `GLOBAL` |
| **Ad Blocker** | `ADBLOCK_ENABLED` | `true` |
| **Scoring** | `SCORE_ALIVE`, `SCORE_SPEED_MAX`, `SCORE_RECENCY_MAX`, `SCORE_FAILURE_PENALTY`, `SCORE_SUCCESS_RATE_MAX` | `50`, `25`, `15`, `5`, `10` |

### Update Settings via API
```bash
curl -X POST http://127.0.0.1:9090/api/config \
  -H "Content-Type: application/json" \
  -d '{"HTTP_PROXY_PORT": 9999, "AUTH_ENABLED": false}'
```

---

## 📁 Project Structure

```
Proxy_redirector/
├── main.py                    # Entry point (console + GUI router)
├── config.py                  # Dynamic config system (JSON-backed)
├── requirements.txt           # Python dependencies
│
├── core/                      # Core proxy engine
│   ├── __init__.py            # Package exports
│   ├── proxy_manager.py       # Proxy loading, scoring, sorting, country filtering
│   ├── proxy_checker.py       # Async proxy validation with anonymity & speed check
│   ├── failover_handler.py    # Automatic proxy switching (suggest_switch, refresh_best)
│   ├── adblock_manager.py     # Ad/tracker/malware blocking engine (exact + wildcard)
│   └── proxy_analytics.py     # Historical performance tracking & auto-tagging
│
├── servers/                   # Network servers
│   ├── __init__.py            # Package exports
│   ├── socks5_server.py       # SOCKS5 local tunnel with auth
│   ├── http_proxy_server.py   # HTTP/HTTPS proxy for phones (CONNECT + forwarding)
│   └── api_server.py          # REST API + ProxyEngine orchestrator
│
├── gui/                       # Desktop GUI
│   └── launcher.py            # pywebview window launcher (single-instance, loading screen)
│
├── utils/                     # Utilities
│   └── traffic_logger.py      # Request logging, client stats, per-client tracking
│
├── data/                      # Data files (auto-created)
│   ├── config.json            # Dynamic user settings
│   ├── data.json              # Your proxy list (user-provided)
│   ├── analytics.json         # Proxy historical performance memory
│   ├── proxies_status.json    # Current proxy health status
│   └── blocklist.json         # Ad blocker rules & whitelist
│
└── static/                    # Web dashboard UI
    ├── index.html             # Main dashboard page
    ├── loading.html           # Loading screen (shown during startup)
    ├── css/style.css           # Dashboard styles
    └── js/app.js              # Dashboard JavaScript
```

---

## 📊 Scoring Algorithm

Each proxy receives a score based on:

| Factor | Weight | Details |
|--------|--------|---------|
| Currently alive | +50 | Binary: alive or not |
| Response speed | 0 to +25 | Based on ratio to `SPEED_THRESHOLD_MS` (500ms default) |
| Recency of last success | 0 to +15 | Full points if checked within the last hour, decays linearly |
| Overall success rate | 0 to +10 | `total_successes / total_checks` |
| Consecutive failures | -5 per failure | Stacking penalty |

The highest-scoring proxy is used first. After each check cycle, the fastest alive proxy becomes the active proxy.

### Analytics Reliability Score (0-100)

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Uptime % | 40% | Historical uptime percentage |
| Speed | 30% | `100 - (avg_speed_ms / 5)` |
| Consistency | 20% | Based on coefficient of variation of speed history |
| Recency | 10% | `100 - (hours_since_last_check × 4)` |

---

## 🔌 REST API Reference

All API endpoints are available at `http://127.0.0.1:9090`.

### GET Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/status` | Server status, ports, active proxy, pool summary |
| `/api/proxies` | Proxy table (top 30 sorted by score) |
| `/api/clients` | Currently connected clients |
| `/api/traffic` | Traffic stats + recent requests |
| `/api/config` | Current configuration |
| `/api/blocklist` | Ad blocker rules, whitelist, categories, stats |
| `/api/countries` | Available countries with proxy counts |
| `/api/analytics` | Analytics summary (total tracked, avg speed, best/worst proxy) |
| `/api/analytics/top` | Top 20 proxies by reliability score |
| `/api/analytics/countries` | Performance statistics by country |

### POST Endpoints

| Endpoint | Body | Description |
|----------|------|-------------|
| `/api/start` | — | Start the proxy engine |
| `/api/stop` | — | Stop the proxy engine |
| `/api/config` | `{key: value, ...}` | Update configuration |
| `/api/traffic/clear` | — | Clear traffic logs |
| `/api/blocklist/rules` | `{action, domain, category}` | Add/remove block rule |
| `/api/blocklist/whitelist` | `{action, domain}` | Add/remove whitelist entry |
| `/api/blocklist/toggle` | `{category?, enabled}` | Toggle category or entire blocker |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
