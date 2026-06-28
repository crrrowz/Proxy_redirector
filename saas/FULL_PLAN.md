# 📦 Proxy Redirector SaaS — الخطة الكاملة

> تم الدمج تلقائياً — جميع ملفات `saas/` في ملف واحد

---


# 📦 Proxy Redirector — SaaS Project Structure

> هذا الفولدر يحتوي على الخطط التفصيلية لتحويل المشروع إلى نظام SaaS كامل.
> **لا يحتوي على أكواد** — فقط الأفكار، الصفحات، هيكلية الملفات، والمواصفات.

---

## الفولدرات الثلاثة

```
saas/
│
├── 📁 website/          ← الموقع التسويقي + التنزيلات + الاشتراكات
│   ├── OVERVIEW.md      ← نظرة عامة على الموقع
│   ├── PAGES.md         ← كل صفحة بالتفصيل (المحتوى + العناصر + السلوك)
│   ├── FILE_STRUCTURE.md← هيكلية الملفات والمجلدات
│   ├── DESIGN_SYSTEM.md ← نظام التصميم (الألوان، الخطوط، المكونات)
│   └── SEO_PLAN.md      ← خطة SEO والتسويق
│
├── 📁 client-app/       ← تطبيق العميل (Desktop) للاتصال وبث البروكسي
│   ├── OVERVIEW.md      ← نظرة عامة على التطبيق
│   ├── SCREENS.md       ← كل شاشة بالتفصيل
│   ├── FILE_STRUCTURE.md← هيكلية الملفات
│   ├── FEATURES.md      ← الميزات والسلوكيات
│   └── NETWORK_FLOW.md  ← مسار الاتصال والبث للأجهزة
│
├── 📁 server/           ← البنية التحتية (API + Relay + توزيع البروكسيات)
│   ├── OVERVIEW.md      ← نظرة عامة على السيرفر
│   ├── API_SPEC.md      ← مواصفات كل API endpoint
│   ├── FILE_STRUCTURE.md← هيكلية الملفات
│   ├── DEPLOYMENT.md    ← خطة النشر والتوزيع
│   ├── PROXY_SOURCES.md ← مصادر البروكسيات وإدارتها
│   └── SCALING.md       ← خطة التوسع والمراقبة
│
└── README.md            ← هذا الملف
```

## كيفية الاستخدام

1. **ابدأ بقراءة `OVERVIEW.md`** في كل فولدر لفهم الصورة الكبيرة
2. **انتقل للتفاصيل** (`PAGES.md`, `SCREENS.md`, `API_SPEC.md`)
3. **راجع `FILE_STRUCTURE.md`** لمعرفة الملفات المطلوبة قبل البدء بالبرمجة
4. **ارجع لـ `SAAS_PLAN.md`** في الجذر للمرجع العام

## العلاقة بين الفولدرات

```
                    ┌──────────────┐
                    │   Website    │ ← يعرض الخطط + رابط تنزيل التطبيق
                    │  (Marketing) │ ← يتكامل مع Stripe للدفع
                    └──────┬───────┘
                           │ يوجّه المستخدم للتسجيل والتنزيل
                           ▼
                    ┌──────────────┐
                    │  Client App  │ ← يسجل دخول + يتصل بالسيرفر
                    │  (Desktop)   │ ← يبث البروكسي لأجهزة المستخدم
                    └──────┬───────┘
                           │ JWT Auth + Usage Reports
                           ▼
                    ┌──────────────┐
                    │   Server     │ ← يوفر البروكسيات + يراقب الاستهلاك
                    │ (Backend)    │ ← يدير Relay Servers + يخزّن البيانات
                    └──────────────┘
```


---


# خطة تحويل Proxy Redirector إلى نظام SaaS كامل

> **الحالة:** مسودة v2.0 — آخر تحديث: 2026-06-28

---

## 1. المعمارية العامة (System Architecture)

### النظرة الشاملة

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLOUD INFRASTRUCTURE                          │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────────────┐ │
│  │  Auth (JWT)  │   │  Central API │   │  Proxy Health Worker  │ │
│  │  + OAuth2    │   │  (Go / Fiber)│   │  (Background Cron)    │ │
│  └──────┬──────┘   └──────┬───────┘   └──────────┬────────────┘ │
│         │                 │                       │              │
│         └────────┬────────┘                       │              │
│                  │                                │              │
│         ┌───────▼────────┐               ┌───────▼────────┐     │
│         │  PostgreSQL    │               │  Redis Cache    │     │
│         │  (Supabase)    │               │  (Sessions/     │     │
│         │                │               │   Rate Limits)  │     │
│         └────────────────┘               └────────────────┘     │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────┐    │
│  │  Relay Servers (VPS) │   │  Admin Dashboard (Web)       │    │
│  │  Multi-Region        │   │  Next.js / React             │    │
│  │  (US, EU, Asia)      │   └──────────────────────────────┘    │
│  └──────────┬───────────┘                                       │
└─────────────┼───────────────────────────────────────────────────┘
              │
    ┌─────────▼──────────┐
    │  Client App (Wails)│
    │  Desktop / Mobile  │
    │  SOCKS5 + HTTP     │
    └────────────────────┘
```

### أ. الخادم المركزي (Central Backend)

| المكون | التقنية | المسؤولية |
|--------|---------|-----------|
| API Gateway | Go + Fiber / Chi | REST + WebSocket, JWT Auth, Rate Limiting |
| Database | PostgreSQL (Supabase) | Users, Subscriptions, Proxies, Sessions, Audit Logs |
| Cache | Redis | JWT Blacklist, Rate Limits, Proxy Assignment Cache, Session Tokens |
| Queue | Redis Pub/Sub أو NATS | Proxy health events, Usage reporting |
| Object Storage | S3 / Supabase Storage | Blocklists, Analytics Exports, Client Binaries |

### ب. Relay Servers (خوادم الترحيل)

- VPS مستقلة في مناطق جغرافية مختلفة (US-East, EU-West, Asia-Pacific)
- تعمل كنقاط WireGuard/SOCKS5 وسيطة
- العميل لا يعرف IP البروكسي النهائي أبداً
- تتواصل مع Central API عبر gRPC داخلي مشفر

### ج. تطبيق العميل (Client Application)

| الميزة | التفاصيل |
|--------|----------|
| التقنية | Wails v2 (Go Backend + React Frontend) |
| البروتوكولات | SOCKS5 + HTTP Proxy على localhost |
| المصادقة | JWT Token + Device Fingerprint |
| التحديث | Auto-updater مدمج |
| الأنظمة | Windows, macOS, Linux, Android (مستقبلاً) |

---

## 2. نموذج الأعمال والتسعير (Business Model)

### خطط الاشتراك

| الخطة | السعر/شهر | الباندويث | المناطق | الأجهزة | الميزات |
|-------|-----------|-----------|---------|---------|---------|
| **Free** | $0 | 500MB | منطقة واحدة | 1 | سرعة محدودة، إعلانات في التطبيق |
| **Basic** | $5 | 50GB | 3 مناطق | 2 | بدون إعلانات، Ad Blocker |
| **Pro** | $12 | 200GB | جميع المناطق | 5 | أولوية السرعة، API Access |
| **Business** | $30 | 1TB | جميع المناطق | 15 | Dedicated IPs, SLA 99.9% |
| **Enterprise** | Custom | Unlimited | Custom | Unlimited | White-label, On-premise relay |

### نموذج الإيرادات الإضافية

- **Add-on Bandwidth**: $2/50GB إضافية
- **Dedicated IP**: $5/شهر لكل IP ثابت
- **API Access (المطورين)**: مضمن في Pro+
- **Reseller Program**: خصم 40% للموزعين (10+ تراخيص)

---

## 3. نظام الصلاحيات والأدوار (RBAC)

```
Super Admin ──► Platform Admin ──► Reseller ──► Client
    │               │                 │           │
    │               │                 │           ├── Connect/Disconnect
    │               │                 │           ├── View Usage
    │               │                 │           └── Change Region
    │               │                 │
    │               │                 ├── Manage Sub-clients
    │               │                 ├── View Revenue
    │               │                 └── Custom Branding
    │               │
    │               ├── Manage Users
    │               ├── View Analytics
    │               └── Manage Proxies
    │
    ├── Full System Access
    ├── Billing & Revenue
    ├── Infrastructure
    └── Relay Server Management
```

### جدول الصلاحيات

| القدرة | Super Admin | Platform Admin | Reseller | Client |
|--------|:-----------:|:--------------:|:--------:|:------:|
| إدارة البنية التحتية | ✅ | ❌ | ❌ | ❌ |
| رفع قوائم البروكسيات | ✅ | ✅ | ❌ | ❌ |
| إدارة المستخدمين | ✅ | ✅ | ✅ (فرعي) | ❌ |
| عرض الإحصائيات الشاملة | ✅ | ✅ | ✅ (فرعي) | ❌ |
| إدارة الفواتير | ✅ | ❌ | ❌ | ❌ |
| الاتصال بالبروكسي | ✅ | ✅ | ✅ | ✅ |
| عرض الاستهلاك الشخصي | ✅ | ✅ | ✅ | ✅ |

---

## 4. واجهات API الكاملة

### 4.1 المصادقة (Authentication)

| Endpoint | Method | وصف |
|----------|--------|-----|
| `/api/v1/auth/register` | POST | تسجيل حساب جديد (email, password) |
| `/api/v1/auth/login` | POST | تسجيل دخول → JWT (access + refresh tokens) |
| `/api/v1/auth/refresh` | POST | تجديد Access Token عبر Refresh Token |
| `/api/v1/auth/logout` | POST | إبطال الجلسة + إضافة Token لـ Blacklist |
| `/api/v1/auth/forgot-password` | POST | إرسال رابط إعادة تعيين كلمة المرور |
| `/api/v1/auth/reset-password` | POST | إعادة تعيين كلمة المرور |
| `/api/v1/auth/verify-email` | GET | تأكيد البريد الإلكتروني |
| `/api/v1/auth/oauth/{provider}` | GET | تسجيل دخول عبر Google/GitHub |

### 4.2 العميل (Client)

| Endpoint | Method | وصف |
|----------|--------|-----|
| `/api/v1/proxy/connect` | POST | طلب اتصال بروكسي (region, protocol) |
| `/api/v1/proxy/disconnect` | POST | قطع الاتصال |
| `/api/v1/proxy/regions` | GET | المناطق المتاحة مع حالة كل منطقة |
| `/api/v1/user/profile` | GET | بيانات الحساب |
| `/api/v1/user/usage` | GET | الاستهلاك الحالي والحد المسموح |
| `/api/v1/user/usage/report` | POST | الإبلاغ عن استهلاك (من التطبيق) |
| `/api/v1/user/devices` | GET | الأجهزة المسجلة |
| `/api/v1/user/devices/{id}` | DELETE | حذف جهاز |
| `/api/v1/subscription/current` | GET | تفاصيل الاشتراك الحالي |
| `/api/v1/subscription/upgrade` | POST | ترقية الباقة |

### 4.3 الإدارة (Admin)

| Endpoint | Method | وصف |
|----------|--------|-----|
| `/api/v1/admin/users` | GET | قائمة المستخدمين مع فلاتر وترقيم |
| `/api/v1/admin/users/{id}` | GET/PATCH/DELETE | إدارة مستخدم واحد |
| `/api/v1/admin/users/{id}/ban` | POST | حظر مستخدم |
| `/api/v1/admin/proxies` | GET/POST | عرض/رفع قوائم البروكسيات |
| `/api/v1/admin/proxies/import` | POST | استيراد بروكسيات (CSV/JSON/TXT) |
| `/api/v1/admin/relays` | GET | حالة خوادم الترحيل |
| `/api/v1/admin/analytics/overview` | GET | إحصائيات النظام الشاملة |
| `/api/v1/admin/analytics/revenue` | GET | تقارير الإيرادات |
| `/api/v1/admin/settings` | GET/PATCH | إعدادات النظام العامة |

### 4.4 Billing (الفوترة)

| Endpoint | Method | وصف |
|----------|--------|-----|
| `/api/v1/billing/plans` | GET | الخطط المتاحة |
| `/api/v1/billing/checkout` | POST | إنشاء جلسة دفع (Stripe/Paddle) |
| `/api/v1/billing/webhook` | POST | استقبال أحداث بوابة الدفع |
| `/api/v1/billing/invoices` | GET | فواتير المستخدم |
| `/api/v1/billing/cancel` | POST | إلغاء الاشتراك |

---

## 5. أمن الاتصال (Connection Security)

### المعمارية المختارة: Hybrid Relay

```
Client App ──[TLS 1.3]──► Relay Server ──[Internal]──► Target Proxy ──► Internet
     │                         │
     │  مشفر بالكامل           │  الـ Client لا يعرف
     │  + Certificate Pinning  │  عنوان البروكسي النهائي
     │                         │
     └─── Usage Report ────────► Central API
```

### طبقات الأمان

| الطبقة | التقنية | الغرض |
|--------|---------|-------|
| Transport | TLS 1.3 + Certificate Pinning | تشفير الاتصال بين Client و Relay |
| Authentication | JWT + Device Fingerprint | منع مشاركة الحسابات |
| Authorization | RBAC + Usage Quotas | التحكم في الصلاحيات والاستهلاك |
| Rate Limiting | Redis + Token Bucket | حماية من إساءة الاستخدام |
| IP Protection | Relay-only model | إخفاء عناوين البروكسيات الأصلية |
| Anti-Tampering | Binary Obfuscation + Checksum | حماية تطبيق العميل من التعديل |
| Audit | Structured Logging + Alerts | تتبع كل العمليات الحساسة |

### JWT Token Structure

```json
{
  "sub": "user_uuid",
  "role": "client",
  "plan": "pro",
  "device_id": "fingerprint_hash",
  "bandwidth_remaining_gb": 185.5,
  "allowed_regions": ["US", "EU", "AS"],
  "max_devices": 5,
  "exp": 1735689600,
  "iat": 1735603200
}
```

---

## 6. هيكلية قاعدة البيانات (Database Schema)

### ERD مبسط

```
users ─┬──< subscriptions
       ├──< sessions
       ├──< devices
       ├──< usage_logs
       └──< audit_logs

plans ──< subscriptions

proxies ──< proxy_health_checks
        ──< sessions

relay_servers ──< proxies (region assignment)
```

### الجداول

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | bcrypt |
| role | ENUM | super_admin, admin, reseller, client |
| status | ENUM | active, suspended, banned |
| email_verified | BOOLEAN | DEFAULT false |
| parent_id | UUID | FK → users (للموزعين) |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

#### `plans`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(50) | free, basic, pro, business, enterprise |
| price_cents | INTEGER | السعر بالسنتات |
| bandwidth_gb | INTEGER | الحد الشهري |
| max_devices | INTEGER | |
| max_regions | INTEGER | |
| features | JSONB | ميزات إضافية |
| is_active | BOOLEAN | |

#### `subscriptions`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users |
| plan_id | UUID | FK → plans |
| status | ENUM | active, cancelled, past_due, trial |
| stripe_subscription_id | VARCHAR | |
| current_period_start | TIMESTAMPTZ | |
| current_period_end | TIMESTAMPTZ | |
| bandwidth_used_bytes | BIGINT | DEFAULT 0 |
| created_at | TIMESTAMPTZ | |

#### `devices`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users |
| fingerprint | VARCHAR(255) | Device hash |
| name | VARCHAR(100) | "Hassan's PC" |
| os | VARCHAR(50) | Windows 11, macOS, etc. |
| last_active | TIMESTAMPTZ | |
| is_active | BOOLEAN | |

#### `proxies`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| ip_address | INET | |
| port | INTEGER | |
| protocol | ENUM | socks5, socks4, http, https |
| country | CHAR(2) | ISO 3166-1 |
| city | VARCHAR(100) | |
| relay_server_id | UUID | FK → relay_servers |
| status | ENUM | active, dead, checking, blacklisted |
| speed_ms | INTEGER | آخر قياس |
| reliability_score | FLOAT | 0-100 |
| last_checked | TIMESTAMPTZ | |
| added_by | UUID | FK → users (admin) |

#### `sessions`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → users |
| device_id | UUID | FK → devices |
| proxy_id | UUID | FK → proxies |
| relay_server_id | UUID | FK → relay_servers |
| connected_at | TIMESTAMPTZ | |
| disconnected_at | TIMESTAMPTZ | NULL = active |
| bytes_up | BIGINT | |
| bytes_down | BIGINT | |
| region | CHAR(2) | |

#### `relay_servers`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| hostname | VARCHAR(255) | |
| ip_address | INET | |
| region | VARCHAR(20) | us-east, eu-west, etc. |
| capacity | INTEGER | max concurrent connections |
| current_load | INTEGER | |
| status | ENUM | online, maintenance, offline |
| last_heartbeat | TIMESTAMPTZ | |

#### `usage_logs` (Partitioned by month)
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | PK |
| user_id | UUID | FK → users |
| session_id | UUID | FK → sessions |
| bytes_transferred | BIGINT | |
| recorded_at | TIMESTAMPTZ | |

#### `audit_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | PK |
| actor_id | UUID | FK → users |
| action | VARCHAR(100) | user.login, proxy.assign, etc. |
| target_type | VARCHAR(50) | user, proxy, subscription |
| target_id | UUID | |
| metadata | JSONB | |
| ip_address | INET | |
| created_at | TIMESTAMPTZ | |

### Indexes

```sql
CREATE INDEX idx_sessions_user_active ON sessions(user_id) WHERE disconnected_at IS NULL;
CREATE INDEX idx_proxies_region_status ON proxies(country, status) WHERE status = 'active';
CREATE INDEX idx_usage_logs_user_month ON usage_logs(user_id, recorded_at);
CREATE INDEX idx_subscriptions_active ON subscriptions(user_id) WHERE status = 'active';
CREATE INDEX idx_audit_actor ON audit_logs(actor_id, created_at DESC);
```

---

## 7. البنية التحتية والنشر (Infrastructure & Deployment)

### Stack التقني

| الطبقة | التقنية | الاستضافة |
|--------|---------|-----------|
| Central API | Go (Fiber) | Railway / Fly.io / VPS |
| Database | PostgreSQL 16 | Supabase |
| Cache | Redis 7 | Upstash / Railway |
| Relay Servers | Go binary | Hetzner / DigitalOcean VPS |
| Admin Dashboard | Next.js 14 | Vercel |
| Client App | Wails v2 (Go + React) | GitHub Releases |
| CI/CD | GitHub Actions | Auto-build + deploy |
| Monitoring | Grafana + Prometheus | Self-hosted |
| Payments | Stripe / Paddle | SaaS |
| Email | Resend / Postmark | Transactional |

### Multi-Region Relay Deployment

```
Region          VPS Provider    Specs           Cost/mo
─────────────────────────────────────────────────────
US-East (NYC)   DigitalOcean   2 vCPU, 4GB     $24
EU-West (AMS)   Hetzner        2 vCPU, 4GB     €6.90
Asia (SGP)      DigitalOcean   2 vCPU, 4GB     $24
ME (Bahrain)    Hetzner        2 vCPU, 4GB     €6.90
```

### CI/CD Pipeline

```
Push to main → GitHub Actions:
  ├── Lint + Test (Go)
  ├── Build API Docker Image → Push to Registry
  ├── Build Client Binaries (Windows, macOS, Linux)
  ├── Deploy API to Railway
  ├── Deploy Admin Dashboard to Vercel
  └── Upload Client Binaries to GitHub Releases
```

---

## 8. نظام مراقبة الاستهلاك (Usage Tracking)

### آلية التتبع

```
Client App ──[كل 30 ثانية]──► POST /api/v1/user/usage/report
                                 {
                                   "session_id": "...",
                                   "bytes_up": 1048576,
                                   "bytes_down": 5242880,
                                   "interval_seconds": 30
                                 }
                                       │
                                       ▼
                              Central API:
                              1. التحقق من JWT
                              2. تحديث usage_logs
                              3. تحديث subscription.bandwidth_used_bytes
                              4. إذا تجاوز الحد → إرسال إشعار
                              5. إذا تجاوز 110% → قطع الاتصال
```

### حدود الاستخدام

| الحدث | الإجراء |
|-------|---------|
| 80% من الحد | إشعار تحذيري (Email + In-App) |
| 100% من الحد | تقليل السرعة (Throttle to 1Mbps) |
| 110% من الحد | قطع الاتصال + إشعار بالترقية |
| انتهاء الاشتراك | تحويل لخطة Free تلقائياً |

---

## 9. لوحة تحكم الإدارة (Admin Dashboard)

### الصفحات المطلوبة

| الصفحة | المحتوى |
|--------|---------|
| Overview | إحصائيات سريعة: MAU, Revenue, Active Connections, Bandwidth Used |
| Users | جدول المستخدمين + فلاتر + إجراءات (حظر، تعديل باقة، حذف) |
| Subscriptions | إدارة الخطط والأسعار |
| Proxies | رفع/إدارة قوائم البروكسيات، حالة الصحة |
| Relay Servers | حالة كل خادم ترحيل، الحمل، المنطقة |
| Analytics | رسوم بيانية: Traffic trends, Revenue growth, Churn rate |
| Audit Log | سجل كل العمليات الحساسة |
| Settings | إعدادات النظام العامة |

---

## 10. الخطوات التنفيذية (Implementation Roadmap)

### المرحلة 1: الأساس (4-6 أسابيع)
- [ ] إنشاء مشروع Go API (Fiber + GORM)
- [ ] هيكلة قاعدة البيانات (Migrations)
- [ ] نظام المصادقة (JWT + Refresh Tokens)
- [ ] CRUD للمستخدمين والخطط
- [ ] نقل منطق Proxy Checker من Python إلى Go
- [ ] Endpoint: `/api/v1/proxy/connect` (Direct Assignment أولاً)

### المرحلة 2: تطبيق العميل SaaS (3-4 أسابيع)
- [ ] تجريد Client App من إدارة البروكسيات المحلية
- [ ] شاشة تسجيل دخول + Registration
- [ ] شاشة اختيار المنطقة + اتصال بنقرة واحدة
- [ ] تتبع الاستهلاك وإرسال التقارير للخادم
- [ ] Device Fingerprinting + حد الأجهزة
- [ ] Auto-updater

### المرحلة 3: Relay Servers (3-4 أسابيع)
- [ ] بناء Relay Server binary (Go)
- [ ] تشفير TLS 1.3 بين Client و Relay
- [ ] gRPC داخلي بين Relay و Central API
- [ ] نشر أول 2 relay servers (US + EU)
- [ ] Load balancing وتوزيع الحمل
- [ ] Health monitoring + Auto-failover

### المرحلة 4: الفوترة والاشتراكات (2-3 أسابيع)
- [ ] تكامل Stripe/Paddle
- [ ] Webhook handlers للدفع
- [ ] نظام الفواتير التلقائي
- [ ] إدارة الترقية/التخفيض
- [ ] فترة تجريبية (7 أيام)
- [ ] صفحة Pricing عامة

### المرحلة 5: لوحة تحكم الإدارة (3-4 أسابيع)
- [ ] Next.js Admin Dashboard
- [ ] إدارة المستخدمين (CRUD + Ban + Modify Plan)
- [ ] إدارة البروكسيات (Import/Health/Stats)
- [ ] Analytics وتقارير الإيرادات
- [ ] Audit Logging
- [ ] إدارة Relay Servers

### المرحلة 6: التوسع والتحسين (مستمر)
- [ ] تطبيق Android (Flutter أو React Native)
- [ ] برنامج الموزعين (Reseller Panel)
- [ ] White-label solution
- [ ] نشر relay servers إضافية
- [ ] تحسين الأداء وتقليل Latency
- [ ] نظام تذاكر دعم مدمج

---

## 11. تقدير التكاليف الشهرية

| البند | التكلفة المتوقعة |
|-------|------------------|
| VPS (4 relay servers) | ~$60 |
| Supabase (Pro) | $25 |
| Redis (Upstash) | $10 |
| Railway (API) | $20 |
| Vercel (Dashboard) | $0 (Hobby) → $20 (Pro) |
| Stripe fees | 2.9% + $0.30/transaction |
| Email (Resend) | $0 → $20 |
| Domain + SSL | ~$15/year |
| **المجموع** | **~$135-155/شهر** |

**نقطة التعادل:** ~28 مشترك Basic أو ~12 مشترك Pro

---

## 12. مقاييس النجاح (KPIs)

| المقياس | الهدف (6 أشهر) |
|---------|----------------|
| MAU (Monthly Active Users) | 500+ |
| MRR (Monthly Recurring Revenue) | $2,000+ |
| Churn Rate | < 8% |
| Average Session Duration | > 2 hours |
| Uptime (Relay Servers) | 99.5%+ |
| Proxy Pool Health | > 70% alive |
| Average Latency | < 200ms |
| Customer Support Response | < 4 hours |

---

## 13. المخاطر والتخفيف

| المخاطر | الاحتمال | التأثير | التخفيف |
|---------|----------|---------|---------|
| تسريب عناوين البروكسيات | متوسط | عالي | Relay-only model, Binary obfuscation |
| إساءة استخدام (Spam/Abuse) | عالي | متوسط | Rate limiting, Usage monitoring, ToS |
| عدم كفاية البروكسيات | متوسط | عالي | مصادر متعددة, شراء بروكسيات premium |
| مشاكل قانونية | منخفض | عالي | ToS واضحة, GDPR compliance, AUP |
| تعطل خادم ترحيل | متوسط | عالي | Multi-region, Auto-failover |
| منافسة شرسة | عالي | متوسط | ميزات فريدة, أسعار تنافسية, UX ممتاز |

---

## قرارات معمارية مطلوبة ⚠️

1. **Relay vs Direct Assignment:** الخطة تفترض Relay. هل نبدأ بـ Direct Assignment مؤقتاً لتسريع الإطلاق؟
2. **بوابة الدفع:** Stripe أو Paddle؟ (Paddle يدعم ضريبة المبيعات تلقائياً)
3. **Admin Dashboard:** Next.js مستقل أو مدمج في Central API؟
4. **تطبيق الهاتف:** Flutter, React Native, أو Wails mobile؟
5. **مصدر البروكسيات:** scraping فقط أم شراء proxy pools من موردين؟


---




================================================================================

# 🌐 الموقع التسويقي (Website)

================================================================================



<!-- ═══ website/DESIGN_SYSTEM.md ═══ -->


# 🎨 نظام التصميم (Design System)

---

## الألوان

### الألوان الأساسية (Dark Theme — الافتراضي)

| الاسم | Hex | الاستخدام |
|-------|-----|-----------|
| Background | `#0a0e17` | خلفية الصفحة الرئيسية |
| Surface | `#111827` | الكروت والأقسام |
| Surface Elevated | `#1f2937` | Modals, Dropdowns |
| Border | `#374151` | حدود الكروت |
| Text Primary | `#f9fafb` | النص الرئيسي |
| Text Secondary | `#9ca3af` | النص الثانوي |
| Text Muted | `#6b7280` | Labels, captions |

### الألوان المميزة (Brand)

| الاسم | Hex | الاستخدام |
|-------|-----|-----------|
| Primary | `#6366f1` | الأزرار الرئيسية (Indigo) |
| Primary Hover | `#4f46e5` | Hover state |
| Primary Light | `#818cf8` | روابط، أيقونات |
| Accent | `#06b6d4` | عناصر مميزة (Cyan) |
| Success | `#10b981` | حالة متصل، نجاح |
| Warning | `#f59e0b` | تحذيرات |
| Danger | `#ef4444` | أخطاء، حذف |

### Gradient الرئيسي
```css
background: linear-gradient(135deg, #6366f1 0%, #06b6d4 50%, #8b5cf6 100%);
```

---

## الخطوط

| الاستخدام | الخط | الوزن |
|-----------|------|-------|
| العناوين (EN) | Inter | Bold (700) |
| النص (EN) | Inter | Regular (400), Medium (500) |
| العناوين (AR) | IBM Plex Sans Arabic | Bold (700) |
| النص (AR) | IBM Plex Sans Arabic | Regular (400) |
| الأكواد | JetBrains Mono | Regular (400) |

### أحجام الخطوط

| Token | الحجم | الاستخدام |
|-------|-------|-----------|
| `text-xs` | 12px | Badges, captions |
| `text-sm` | 14px | Labels, metadata |
| `text-base` | 16px | Body text |
| `text-lg` | 18px | Subtitles |
| `text-xl` | 20px | Card titles |
| `text-2xl` | 24px | Section titles |
| `text-3xl` | 30px | Page titles |
| `text-4xl` | 36px | Hero subtitle |
| `text-5xl` | 48px | Hero title |
| `text-6xl` | 60px | Landing hero |

---

## المكونات

### الأزرار

| النوع | الشكل | الاستخدام |
|-------|-------|-----------|
| Primary | خلفية Primary + نص أبيض + rounded-xl | CTA الرئيسي |
| Secondary | حدود Primary + نص Primary + شفاف | CTA ثانوي |
| Ghost | بدون خلفية + نص Secondary | روابط، إجراءات ثانوية |
| Danger | خلفية Danger + نص أبيض | حذف، إلغاء |
| Icon | دائرة + أيقونة فقط | أزرار الأدوات |

### خصائص الأزرار
- `border-radius`: 12px (rounded-xl)
- `padding`: 12px 24px (md), 16px 32px (lg)
- `transition`: 150ms ease
- `hover`: scale(1.02) + تغيير اللون
- `active`: scale(0.98)
- `disabled`: opacity 50%

### الكروت

| النوع | الخصائص |
|-------|---------|
| Default | Surface bg + Border + rounded-2xl + p-6 |
| Elevated | Surface Elevated bg + shadow-xl |
| Glass | backdrop-blur-xl + bg-white/5 + border-white/10 |
| Gradient Border | حدود gradient + شفاف |

### الحقول (Inputs)

- خلفية: Surface
- حدود: Border → Primary عند Focus
- rounded-xl
- padding: 12px 16px
- placeholder: Text Muted
- Error state: حدود Danger + رسالة خطأ أسفله

---

## الحركات (Animations)

| الحركة | الاستخدام | المواصفات |
|--------|-----------|-----------|
| Fade In Up | ظهور الأقسام عند Scroll | translateY(20px) → 0, opacity 0 → 1, 600ms |
| Scale In | ظهور الكروت | scale(0.95) → 1, 300ms |
| Slide In | القوائم الجانبية | translateX(-100%) → 0, 300ms |
| Pulse | شارة "متصل" | scale(1) → 1.05, loop |
| Count Up | الأرقام في Landing | 0 → target, 2000ms |
| Gradient Shift | خلفية Hero | gradient position animation, 8s loop |
| Skeleton | Loading states | shimmer animation |

---

## Responsive Breakpoints

| الاسم | العرض | الأجهزة |
|-------|-------|---------|
| `sm` | 640px | هواتف كبيرة |
| `md` | 768px | تابلت |
| `lg` | 1024px | لابتوب |
| `xl` | 1280px | شاشة عادية |
| `2xl` | 1536px | شاشة كبيرة |

---

## الأيقونات

- مكتبة: **Lucide Icons** (متوافقة مع React)
- الحجم الافتراضي: 20px
- اللون: يرث من النص
- Stroke width: 1.5

---

## صور الإلهام (Design References)

| الموقع | السبب |
|--------|-------|
| nordvpn.com | Hero + Pricing layout |
| linear.app | Dashboard UI + animations |
| vercel.com | Typography + dark theme |
| stripe.com | Pricing page + docs |
| tailwindcss.com | Docs sidebar layout |


---


<!-- ═══ website/FILE_STRUCTURE.md ═══ -->


# 📁 هيكلية ملفات الموقع

```
website/
├── public/
│   ├── favicon.ico
│   ├── og-image.png              # صورة المشاركة على السوشال
│   ├── robots.txt
│   ├── sitemap.xml
│   └── images/
│       ├── hero-mockup.png
│       ├── logo.svg
│       ├── logo-dark.svg
│       └── platforms/
│           ├── windows.svg
│           ├── macos.svg
│           └── linux.svg
│
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx             # Root layout (Header + Footer)
│   │   ├── page.tsx               # Landing Page (/)
│   │   ├── globals.css
│   │   │
│   │   ├── (marketing)/           # صفحات عامة بدون auth
│   │   │   ├── features/page.tsx
│   │   │   ├── pricing/page.tsx
│   │   │   ├── download/page.tsx
│   │   │   ├── about/page.tsx
│   │   │   ├── contact/page.tsx
│   │   │   ├── privacy/page.tsx
│   │   │   ├── terms/page.tsx
│   │   │   └── refund/page.tsx
│   │   │
│   │   ├── (auth)/                # صفحات المصادقة
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   ├── reset-password/page.tsx
│   │   │   └── verify-email/page.tsx
│   │   │
│   │   ├── dashboard/             # لوحة تحكم المستخدم (محمية)
│   │   │   ├── layout.tsx         # Sidebar layout
│   │   │   ├── page.tsx           # Dashboard home
│   │   │   ├── subscription/page.tsx
│   │   │   ├── devices/page.tsx
│   │   │   ├── settings/page.tsx
│   │   │   └── support/
│   │   │       ├── page.tsx       # قائمة التذاكر
│   │   │       └── [id]/page.tsx  # تذكرة واحدة
│   │   │
│   │   ├── blog/
│   │   │   ├── page.tsx           # قائمة المقالات
│   │   │   └── [slug]/page.tsx    # مقال واحد
│   │   │
│   │   ├── docs/
│   │   │   ├── layout.tsx         # Sidebar docs layout
│   │   │   └── [...slug]/page.tsx # صفحات التوثيق الديناميكية
│   │   │
│   │   └── api/                   # API Routes (BFF)
│   │       ├── auth/
│   │       │   ├── login/route.ts
│   │       │   ├── register/route.ts
│   │       │   └── callback/route.ts
│   │       ├── stripe/
│   │       │   └── webhook/route.ts
│   │       └── download/
│   │           └── route.ts       # Proxy download links
│   │
│   ├── components/
│   │   ├── ui/                    # مكونات أساسية
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── Accordion.tsx
│   │   │   ├── Toggle.tsx
│   │   │   └── ProgressBar.tsx
│   │   │
│   │   ├── layout/                # مكونات البنية
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MobileMenu.tsx
│   │   │
│   │   ├── landing/               # مكونات الصفحة الرئيسية
│   │   │   ├── HeroSection.tsx
│   │   │   ├── TrustedBy.tsx
│   │   │   ├── HowItWorks.tsx
│   │   │   ├── FeaturesGrid.tsx
│   │   │   ├── PricingPreview.tsx
│   │   │   ├── Testimonials.tsx
│   │   │   ├── FAQSection.tsx
│   │   │   └── CTASection.tsx
│   │   │
│   │   ├── pricing/
│   │   │   ├── PlanCard.tsx
│   │   │   ├── PlanToggle.tsx
│   │   │   └── FeatureComparison.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   ├── UsageMeter.tsx
│   │   │   ├── StatsCard.tsx
│   │   │   ├── UsageChart.tsx
│   │   │   ├── DeviceList.tsx
│   │   │   └── ActivityFeed.tsx
│   │   │
│   │   └── auth/
│   │       ├── LoginForm.tsx
│   │       ├── RegisterForm.tsx
│   │       ├── OAuthButtons.tsx
│   │       └── PasswordStrength.tsx
│   │
│   ├── lib/
│   │   ├── supabase.ts            # Supabase client
│   │   ├── stripe.ts              # Stripe client
│   │   ├── api.ts                 # Central API client
│   │   ├── auth.ts                # Auth helpers
│   │   └── utils.ts               # Utility functions
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useSubscription.ts
│   │   ├── useUsage.ts
│   │   └── useDevices.ts
│   │
│   ├── content/
│   │   ├── blog/                  # MDX blog posts
│   │   │   ├── why-proxy-2026.mdx
│   │   │   └── vpn-vs-proxy.mdx
│   │   └── docs/                  # MDX documentation
│   │       ├── getting-started/
│   │       ├── device-setup/
│   │       ├── features/
│   │       ├── api-reference/
│   │       └── troubleshooting/
│   │
│   ├── styles/
│   │   └── globals.css
│   │
│   └── types/
│       ├── user.ts
│       ├── plan.ts
│       ├── subscription.ts
│       └── device.ts
│
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.local                     # API keys (Stripe, Supabase, etc.)
```


---


<!-- ═══ website/OVERVIEW.md ═══ -->


# 🌐 الموقع التسويقي — نظرة عامة

## الغرض

موقع ويب عام يمثّل الواجهة الرسمية لمنتج **Proxy Redirector SaaS**:
- تعريف المنتج وميزاته
- عرض خطط الأسعار
- تنزيل تطبيق العميل (Windows, macOS, Linux)
- تسجيل الحسابات وإدارة الاشتراكات
- دعم العملاء والتوثيق
- لوحة تحكم المستخدم (بيانات الحساب، الاستهلاك، الأجهزة)

---

## الجمهور المستهدف

| الشريحة | الاحتياج |
|---------|----------|
| مستخدم عادي | تصفح آمن، تجاوز حجب، خصوصية |
| لاعب (Gamer) | تقليل Ping، تغيير المنطقة |
| مطور | API Access، تكامل مع أدواته |
| شركة صغيرة | حماية الموظفين، IP ثابت |
| موزع (Reseller) | شراء بالجملة وإعادة البيع |

---

## التقنية المقترحة

| العنصر | الخيار | السبب |
|--------|--------|-------|
| Framework | Next.js 14 (App Router) | SSR/SSG للـ SEO + React ecosystem |
| Styling | Tailwind CSS 4 | سرعة التطوير + responsive |
| Auth | Supabase Auth أو NextAuth.js | تكامل مع قاعدة البيانات |
| Payments | Stripe Checkout + Billing Portal | أفضل UX للدفع + إدارة الاشتراكات |
| Hosting | Vercel | أفضل أداء لـ Next.js |
| CMS (Blog) | MDX أو Contentlayer | محتوى ثابت سريع |
| Analytics | Plausible أو PostHog | خصوصية + بدون ملفات تعريف |
| i18n | next-intl | عربي + إنجليزي |

---

## اللغات المدعومة

- **الإنجليزية** (افتراضي) — `/en/*`
- **العربية** (RTL) — `/ar/*`

---

## أقسام الموقع الرئيسية

```
الصفحات العامة (بدون تسجيل دخول)
├── الصفحة الرئيسية (Landing)
├── الميزات (Features)
├── الأسعار (Pricing)
├── التنزيل (Download)
├── المدونة (Blog)
├── التوثيق (Docs)
├── من نحن (About)
├── سياسة الخصوصية (Privacy)
├── شروط الاستخدام (Terms)
└── تواصل معنا (Contact)

لوحة المستخدم (تحتاج تسجيل دخول)
├── لوحة التحكم (Dashboard)
├── الاشتراك (Subscription)
├── الأجهزة (Devices)
├── الاستهلاك (Usage)
├── إعدادات الحساب (Account Settings)
├── الفواتير (Invoices)
└── الدعم (Support Tickets)

صفحات المصادقة
├── تسجيل الدخول (Login)
├── إنشاء حساب (Register)
├── نسيت كلمة المرور (Forgot Password)
├── إعادة تعيين كلمة المرور (Reset Password)
└── تأكيد البريد (Verify Email)
```

---

## الأولوية

| المرحلة | الصفحات | الأهمية |
|---------|---------|---------|
| 1 (MVP) | Landing, Pricing, Download, Login, Register, Dashboard | 🔴 حرجة |
| 2 | Features, Subscription, Usage, Devices, Account Settings | 🟡 مهمة |
| 3 | Blog, Docs, About, Contact, Invoices, Support | 🟢 تحسينية |

---

## ملاحظات مهمة

- الموقع يجب أن يبدو **احترافي ومتميز** — ليس قالب عادي
- التصميم Dark-first مع إمكانية Light mode
- الـ Landing Page يجب أن تقنع الزائر بالتسجيل خلال 10 ثواني
- صفحة التنزيل تكتشف نظام التشغيل تلقائياً وتعرض الزر المناسب
- الدفع يجب أن يكون بدون مغادرة الموقع (Stripe Embedded Checkout)


---


<!-- ═══ website/PAGES.md ═══ -->


# 📄 صفحات الموقع — التفصيل الكامل

---

## 1. الصفحة الرئيسية (Landing Page) — `/`

### الأقسام بالترتيب

| # | القسم | المحتوى |
|---|-------|---------|
| 1 | **Hero** | عنوان جذاب + وصف + زر "ابدأ مجاناً" + زر "تنزيل" + صورة التطبيق |
| 2 | **Trusted By** | أرقام حية: عدد المستخدمين، الدول، uptime |
| 3 | **How It Works** | 3 خطوات: سجّل → نزّل → اتصل بنقرة |
| 4 | **Features Grid** | 6 كروت ميزات مع أيقونات متحركة |
| 5 | **Speed Demo** | مقارنة سرعة مع/بدون البروكسي |
| 6 | **Pricing Preview** | عرض مختصر لـ 3 خطط + "عرض الكل" |
| 7 | **Testimonials** | 3-4 تقييمات (carousel) |
| 8 | **FAQ** | 5 أسئلة شائعة (accordion) |
| 9 | **CTA** | دعوة نهائية للتسجيل |
| 10 | **Footer** | روابط + سوشال + copyright |

---

## 2. الميزات — `/features`

- Hero: "كل ما تحتاجه في تطبيق واحد"
- أقسام: Privacy, Speed, Ad Blocker, Multi-Device, Failover, Analytics, API
- كل ميزة: أيقونة + عنوان + 3 أسطر + screenshot
- جدول مقارنة مع المنافسين

---

## 3. الأسعار — `/pricing`

- Toggle: شهري / سنوي (خصم 20%)
- 4 كروت: Free, Basic ($5), Pro ($12), Business ($30)
- شارة "الأكثر شعبية" على Pro
- جدول تفصيلي لكل ميزة
- Enterprise: "تواصل معنا"
- ضمان استرجاع 7 أيام

---

## 4. التنزيل — `/download`

- كشف نظام التشغيل تلقائياً
- زر تنزيل رئيسي + أزرار كل الأنظمة
- رقم الإصدار + Changelog
- متطلبات النظام
- 3 خطوات إعداد سريع
- قسم "قريباً على الهاتف" مع waitlist

---

## 5. التوثيق — `/docs`

- Sidebar navigation ثابت
- أقسام: البدء السريع، إعداد الأجهزة، الميزات، API Reference، استكشاف الأخطاء
- بحث فوري
- أمثلة أكواد مع copy button
- "هل كانت مفيدة؟" في كل صفحة

---

## 6. المدونة — `/blog`

- قائمة مقالات (grid)
- تصنيفات: أخبار، شروحات، تحديثات، أمان
- كل مقال: عنوان + غلاف + كاتب + تاريخ + وقت القراءة

---

## 7. صفحات المصادقة

| الصفحة | المسار | العناصر |
|--------|--------|---------|
| تسجيل الدخول | `/login` | Email + Password + Remember Me + OAuth + Forgot Password |
| إنشاء حساب | `/register` | Email + Password + Confirm + Terms + OAuth |
| نسيت كلمة المرور | `/forgot-password` | Email field + زر إرسال |
| إعادة تعيين | `/reset-password` | Password + Confirm |

---

## 8. لوحة تحكم المستخدم — `/dashboard/*`

| الصفحة | المسار | المحتوى |
|--------|--------|---------|
| الرئيسية | `/dashboard` | Welcome card + حالة الاتصال + Usage meter + رسم بياني + نشاط أخير |
| الاشتراك | `/dashboard/subscription` | الخطة الحالية + الاستهلاك + ترقية + إلغاء + طريقة الدفع + الفواتير |
| الأجهزة | `/dashboard/devices` | قائمة الأجهزة + حذف + إعادة تسمية + حد الأجهزة |
| الإعدادات | `/dashboard/settings` | Profile + Password + 2FA + Notifications + Language + Delete Account |
| الدعم | `/dashboard/support` | تذكرة جديدة + قائمة التذاكر + تفاصيل تذكرة |

---

## 9. صفحات قانونية

- سياسة الخصوصية — `/privacy`
- شروط الاستخدام — `/terms`
- سياسة الاسترجاع — `/refund`

---

## 10. صفحات إضافية

- من نحن — `/about`
- تواصل معنا — `/contact` (نموذج + بريد + سوشال)

---

## Navigation

**للزائر:**
```
Logo | الميزات | الأسعار | التوثيق | المدونة | التنزيل | [دخول] | [ابدأ مجاناً]
```

**للمستخدم:**
```
Logo | لوحة التحكم | الاشتراك | التنزيل | التوثيق | [Avatar ▼ → إعدادات / خروج]
```


---


<!-- ═══ website/SEO_PLAN.md ═══ -->


# 🔍 خطة SEO والتسويق

---

## SEO التقني

| العنصر | التنفيذ |
|--------|---------|
| SSR/SSG | كل الصفحات العامة SSG، Dashboard SSR |
| Meta Tags | title + description + og:image لكل صفحة |
| Canonical URLs | `<link rel="canonical">` على كل صفحة |
| Sitemap | `/sitemap.xml` ديناميكي من Next.js |
| Robots.txt | السماح لكل الصفحات العامة، منع `/dashboard/*` |
| Structured Data | JSON-LD: Organization, Product, FAQ, Article |
| i18n hreflang | `x-default` + `ar` + `en` |
| Core Web Vitals | LCP < 2.5s, CLS < 0.1, INP < 200ms |
| Image Optimization | next/image + WebP + lazy loading |

## الكلمات المفتاحية

| الصفحة | Keywords |
|--------|----------|
| Landing | proxy service, secure proxy, fast proxy, private browsing |
| Features | ad blocker proxy, multi-device proxy, auto failover proxy |
| Pricing | cheap proxy service, proxy plans, proxy subscription |
| Download | download proxy app, proxy for windows, proxy for mac |
| Docs | how to setup proxy, proxy setup guide, socks5 setup |

## قنوات التسويق

| القناة | الاستراتيجية |
|--------|-------------|
| SEO/Blog | مقالات أسبوعية عن الخصوصية والأمان |
| Twitter/X | نصائح يومية + تحديثات المنتج |
| Reddit | r/privacy, r/VPN, r/selfhosted |
| Product Hunt | إطلاق رسمي |
| YouTube | فيديوهات شرح الإعداد |
| Referral | برنامج إحالة: شهر مجاني لكل صديق |


---



================================================================================

# 🖥️ تطبيق العميل (Client App)

================================================================================



<!-- ═══ client-app/FEATURES.md ═══ -->


# ⚡ الميزات والسلوكيات

---

## 1. الاتصال بنقرة واحدة (One-Click Connect)

### التسلسل
1. المستخدم يضغط زر الاتصال
2. التطبيق يرسل `POST /api/v1/proxy/connect` مع (region, protocol)
3. السيرفر يختار أفضل Relay Server ويرد بـ (relay_host, relay_port, session_token)
4. التطبيق يفتح TLS tunnel إلى الـ Relay
5. التطبيق يشغل SOCKS5 + HTTP proxy محلياً على `0.0.0.0`
6. أي جهاز على الشبكة يمكنه الاتصال عبر المنافذ المحلية

### إعادة الاتصال التلقائي
- إذا انقطع الـ tunnel: يحاول 3 مرات بفاصل 2 ثانية
- إذا فشل: يطلب relay جديد من السيرفر
- إذا فشل تماماً: يعرض رسالة + يوقف الخوادم المحلية

---

## 2. اختيار المنطقة (Region Selection)

### مصدر البيانات
- `GET /api/v1/proxy/regions` يرد بقائمة المناطق:
  - اسم المنطقة + كود الدولة + عدد الخوادم + الحمل الحالي + متوسط الـ Ping
- المناطق المقفلة (حسب الباقة) تظهر مع 🔒

### "أفضل موقع" (Auto)
- التطبيق يفحص ping لكل relay server عند الفتح
- يختار الأقل تأخيراً
- يعرض: "🚀 أفضل موقع — US East (32ms)"

---

## 3. بث البروكسي (Proxy Broadcasting)

### كيف يعمل
- SOCKS5 server على المنفذ 1080 (قابل للتغيير)
- HTTP proxy server على المنفذ 8080 (قابل للتغيير)
- كلاهما يستمع على `0.0.0.0` (كل الشبكات)
- Traffic يُمرر عبر الـ TLS tunnel إلى الـ Relay Server

### المصادقة المحلية
- Whitelist تلقائي: `192.168.x.x`, `10.x.x.x`, `127.0.0.1`
- اسم مستخدم + كلمة مرور (اختياري، قابل للتعديل)
- الأجهزة على الشبكة المحلية لا تحتاج مصادقة

### تتبع الأجهزة
- كل اتصال وارد يُسجّل: IP + البروتوكول + الهدف
- يُعرض في شاشة "الأجهزة المتصلة"
- إشعار عند اتصال جهاز جديد

### QR Code
- يولّد QR يحتوي على: `proxy_host=192.168.1.100&socks5_port=1080&http_port=8080`
- الهاتف يمسحه ويُعدّ البروكسي تلقائياً (يحتاج تطبيق مساعد أو deep link)

---

## 4. تتبع الاستهلاك (Usage Tracking)

### محلياً
- Go يحسب bytes المرسلة والمستقبلة عبر الـ tunnel
- يُخزّن مؤقتاً في SQLite

### الإرسال للسيرفر
- كل 30 ثانية: `POST /api/v1/user/usage/report`
- يرسل: session_id, bytes_up, bytes_down, interval_seconds
- السيرفر يرد بـ: bandwidth_remaining, status (ok/warning/throttled/exceeded)

### ردود فعل الاستهلاك
| الحالة | الإجراء في التطبيق |
|--------|-------------------|
| ok | لا شيء |
| warning (80%) | إشعار + تحذير في الشاشة الرئيسية |
| throttled (100%) | تقليل السرعة + رسالة "ترقية للمزيد" |
| exceeded (110%) | قطع الاتصال + modal ترقية |

---

## 5. Ad Blocker محلي

- طبقة حجب إعلانات في التطبيق (بالإضافة للحجب على السيرفر)
- يفحص كل طلب DNS/HTTP قبل تمريره
- قائمة الحجب تُحمّل من السيرفر وتُخزّن محلياً
- قابل للتشغيل/الإيقاف من الإعدادات

---

## 6. التحديث التلقائي (Auto-Update)

### الآلية
1. عند الفتح: يفحص `GET /api/v1/app/version`
2. إذا يوجد إصدار أحدث: يعرض modal بالتفاصيل
3. "تحديث الآن": يحمّل الملف في الخلفية + يعرض شريط تقدم
4. بعد التحميل: "إعادة تشغيل لتطبيق التحديث"
5. التطبيق يُغلق ← المُحدّث يستبدل الملفات ← يُعيد التشغيل

### التحقق
- Checksum (SHA256) للتأكد من سلامة الملف
- توقيع رقمي (Code Signing) — Windows + macOS

---

## 7. بدء تلقائي (Auto-Start)

- Windows: إضافة مفتاح Registry في `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- macOS: Login Item
- Linux: `.desktop` file في `~/.config/autostart/`
- اختياري: الاتصال تلقائياً عند البدء (بآخر منطقة مستخدمة)

---

## 8. System Tray

- الأيقونة تبقى في شريط المهام حتى لو أُغلقت النافذة
- القائمة: اتصال/قطع | المنطقة | فتح | خروج
- الأيقونة تتغير لوناً حسب الحالة

---

## 9. Offline Mode

- إذا لا يوجد إنترنت: يعرض آخر حالة معروفة
- لا يمكن الاتصال بدون إنترنت
- إعدادات الحساب تُخزّن محلياً (cache)
- JWT يُجدّد عند عودة الإنترنت

---

## 10. أمان التطبيق

| الإجراء | التفاصيل |
|---------|----------|
| تخزين JWT | OS Keychain (Windows Credential Manager, macOS Keychain) |
| Device Fingerprint | hash من: MAC + CPU + hostname + OS |
| Binary Protection | obfuscation + anti-debugging (إصدار الإنتاج) |
| TLS Pinning | Certificate pinning لعنوان الـ Relay |
| Single Instance | Mutex يمنع تشغيل أكثر من نسخة |


---


<!-- ═══ client-app/FILE_STRUCTURE.md ═══ -->


# 📁 هيكلية ملفات تطبيق العميل

```
client-app/
├── build/                          # مخرجات البناء
│   └── bin/
│
├── frontend/                       # React Frontend (Wails)
│   ├── public/
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── main.tsx                # Entry point
│   │   ├── App.tsx                 # Root component + Router
│   │   ├── globals.css
│   │   │
│   │   ├── screens/                # الشاشات الرئيسية
│   │   │   ├── SplashScreen.tsx    # شاشة التحميل
│   │   │   ├── LoginScreen.tsx     # تسجيل الدخول
│   │   │   ├── HomeScreen.tsx      # الشاشة الرئيسية (زر الاتصال)
│   │   │   ├── DevicesScreen.tsx   # الأجهزة المتصلة
│   │   │   ├── SettingsScreen.tsx  # الإعدادات
│   │   │   ├── AccountScreen.tsx   # الحساب
│   │   │   └── UpdateScreen.tsx    # التحديث
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                 # مكونات أساسية
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Toast.tsx
│   │   │   │   ├── Toggle.tsx
│   │   │   │   ├── ProgressBar.tsx
│   │   │   │   ├── Dropdown.tsx
│   │   │   │   └── QRCode.tsx
│   │   │   │
│   │   │   ├── layout/
│   │   │   │   ├── TitleBar.tsx    # شريط العنوان المخصص (minimize, maximize, close)
│   │   │   │   ├── TabBar.tsx      # التنقل السفلي
│   │   │   │   └── AppLayout.tsx   # Layout عام
│   │   │   │
│   │   │   ├── home/
│   │   │   │   ├── ConnectButton.tsx    # زر الاتصال الدائري
│   │   │   │   ├── RegionSelector.tsx   # اختيار المنطقة
│   │   │   │   ├── StatusBar.tsx        # حالة الاتصال + السرعة
│   │   │   │   └── UsageMeter.tsx       # شريط الاستهلاك
│   │   │   │
│   │   │   ├── devices/
│   │   │   │   ├── DeviceList.tsx       # قائمة الأجهزة المتصلة
│   │   │   │   ├── ConnectionInfo.tsx   # معلومات البث (IP + Ports)
│   │   │   │   └── SetupGuide.tsx       # دليل إعداد سريع
│   │   │   │
│   │   │   └── onboarding/
│   │   │       ├── OnboardingSlides.tsx
│   │   │       └── OnboardingSlide.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useConnection.ts    # حالة الاتصال
│   │   │   ├── useAuth.ts          # المصادقة
│   │   │   ├── useUsage.ts         # الاستهلاك
│   │   │   ├── useRegions.ts       # المناطق المتاحة
│   │   │   ├── useDevices.ts       # الأجهزة المتصلة محلياً
│   │   │   └── useUpdater.ts       # التحديثات
│   │   │
│   │   ├── stores/                 # State management (Zustand)
│   │   │   ├── authStore.ts
│   │   │   ├── connectionStore.ts
│   │   │   └── settingsStore.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── wailsBridge.ts      # Wails Go ↔ JS bindings
│   │   │   ├── api.ts              # HTTP client للسيرفر المركزي
│   │   │   └── utils.ts
│   │   │
│   │   └── types/
│   │       ├── connection.ts
│   │       ├── region.ts
│   │       ├── user.ts
│   │       └── device.ts
│   │
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── vite.config.ts
│
├── internal/                       # Go Backend (Wails)
│   ├── app/
│   │   └── app.go                  # Wails App struct + lifecycle
│   │
│   ├── auth/
│   │   ├── auth.go                 # JWT management (store, refresh, validate)
│   │   ├── device.go               # Device fingerprinting
│   │   └── keychain.go             # Secure token storage (OS keychain)
│   │
│   ├── proxy/
│   │   ├── connector.go            # اتصال بالـ Relay Server
│   │   ├── socks5.go               # SOCKS5 server محلي
│   │   ├── http_proxy.go           # HTTP proxy server محلي
│   │   ├── tunnel.go               # TLS tunnel إلى Relay
│   │   └── adblock.go              # Ad blocker محلي
│   │
│   ├── usage/
│   │   ├── tracker.go              # تتبع الاستهلاك (bytes up/down)
│   │   └── reporter.go             # إرسال التقارير للسيرفر كل 30 ثانية
│   │
│   ├── network/
│   │   ├── clients.go              # تتبع الأجهزة المتصلة محلياً
│   │   └── discovery.go            # اكتشاف IP المحلي + الشبكة
│   │
│   ├── updater/
│   │   └── updater.go              # Auto-update logic
│   │
│   ├── config/
│   │   ├── config.go               # إعدادات التطبيق
│   │   └── store.go                # SQLite local storage
│   │
│   └── tray/
│       └── tray.go                 # System tray icon + menu
│
├── main.go                         # Wails entry point
├── wails.json                      # Wails configuration
├── go.mod
├── go.sum
├── Makefile                        # Build commands
└── .github/
    └── workflows/
        └── release.yml             # CI/CD: build + release
```


---


<!-- ═══ client-app/NETWORK_FLOW.md ═══ -->


# 🔄 مسار الاتصال والبث (Network Flow)

---

## المسار الكامل: من ضغطة الزر إلى الإنترنت

```
[1] المستخدم يضغط "اتصل"
         │
         ▼
[2] POST /api/v1/proxy/connect  ──────►  Central API
    { region: "US", protocol: "socks5" }     │
                                              │  يختار أفضل Relay
                                              │  يُنشئ Session
                                              │  يسجّل في DB
                                              ▼
[3] الرد: ◄──────────────────────────  { relay_host, relay_port,
                                         session_token, expires_at }
         │
         ▼
[4] التطبيق يفتح TLS Tunnel
    إلى relay_host:relay_port
    مع session_token
         │
         ▼
[5] Relay Server يتحقق من الـ Token
    مع Central API (gRPC داخلي)
         │
         ▼
[6] Tunnel جاهز ✅
         │
         ▼
[7] التطبيق يشغّل الخوادم المحلية:
    ├── SOCKS5 على 0.0.0.0:1080
    └── HTTP   على 0.0.0.0:8080
         │
         ▼
[8] أي جهاز على الشبكة يتصل بالمنافذ المحلية
```

---

## مسار طلب واحد (Single Request Flow)

```
📱 الهاتف                    🖥️ التطبيق                    ☁️ Relay              🌐 الهدف
    │                            │                            │                      │
    │  HTTP Request              │                            │                      │
    │  proxy=192.168.1.100:8080  │                            │                      │
    ├───────────────────────────►│                            │                      │
    │                            │                            │                      │
    │                            │  [Ad Block Check]          │                      │
    │                            │  محظور؟ → رفض + log       │                      │
    │                            │  مسموح؟ ↓                  │                      │
    │                            │                            │                      │
    │                            │  Forward via TLS Tunnel    │                      │
    │                            ├───────────────────────────►│                      │
    │                            │                            │                      │
    │                            │                            │  Forward to Proxy    │
    │                            │                            ├─────────────────────►│
    │                            │                            │                      │
    │                            │                            │  Response            │
    │                            │                            │◄─────────────────────┤
    │                            │                            │                      │
    │                            │  Response via Tunnel       │                      │
    │                            │◄───────────────────────────┤                      │
    │                            │                            │                      │
    │                            │  [Count bytes]             │                      │
    │                            │  [Update usage tracker]    │                      │
    │                            │                            │                      │
    │  HTTP Response             │                            │                      │
    │◄───────────────────────────┤                            │                      │
    │                            │                            │                      │
```

---

## مسار تقرير الاستهلاك (Usage Reporting)

```
كل 30 ثانية:

🖥️ التطبيق ──► POST /api/v1/user/usage/report ──► ☁️ Central API
                {                                        │
                  session_id: "xxx",                     │  تحديث usage_logs
                  bytes_up: 1048576,                     │  تحديث subscription
                  bytes_down: 5242880                    │  فحص الحدود
                }                                        │
                                                         ▼
                ◄── الرد ─────────────────────────  { status: "ok",
                                                      bandwidth_remaining_gb: 187.5 }
```

---

## مسار التبديل التلقائي (Auto-Failover)

```
[1] Tunnel يسقط (timeout / connection reset)
         │
         ▼
[2] التطبيق يحاول إعادة الاتصال بنفس الـ Relay
    (3 محاولات × 2 ثانية)
         │
    ┌────┴────┐
    نجح       فشل
    │         │
    ▼         ▼
  متصل ✅   [3] POST /api/v1/proxy/connect
              يطلب Relay جديد
                   │
              ┌────┴────┐
              نجح       فشل
              │         │
              ▼         ▼
            متصل ✅   [4] إشعار للمستخدم
                       "فشل الاتصال بكل الخوادم"
                       زر "إعادة المحاولة"
```

---

## مسار بث البروكسي للشبكة المحلية

```
شبكة المستخدم المحلية:

📡 الراوتر (192.168.1.1)
    │
    ├── 🖥️ الكمبيوتر (التطبيق) — 192.168.1.100
    │       ├── SOCKS5 :1080 ← مفتوح لكل الشبكة
    │       └── HTTP   :8080 ← مفتوح لكل الشبكة
    │
    ├── 📱 هاتف 1 (Android) — 192.168.1.50
    │       └── إعدادات WiFi → Proxy: 192.168.1.100:8080
    │
    ├── 📱 هاتف 2 (iOS) — 192.168.1.51
    │       └── إعدادات WiFi → HTTP Proxy: 192.168.1.100:8080
    │
    ├── 🖥️ كمبيوتر 2 — 192.168.1.102
    │       └── Proxifier → SOCKS5: 192.168.1.100:1080
    │
    └── 📺 Smart TV — 192.168.1.60
            └── لا يدعم البروكسي مباشرة
                (يحتاج إعداد DNS أو Router-level proxy)
```

### ملاحظة عن الاستهلاك
- **كل الأجهزة** تُحسب على حساب واحد
- التطبيق يحسب إجمالي الـ bytes عبر كل المنافذ
- السيرفر لا يعرف عدد الأجهزة المحلية — يرى فقط tunnel واحد


---


<!-- ═══ client-app/OVERVIEW.md ═══ -->


# 🖥️ تطبيق العميل — نظرة عامة

## الغرض

تطبيق سطح مكتب يُثبّته المستخدم النهائي للاتصال بخدمة البروكسي. يتواصل مع السيرفر المركزي للحصول على بروكسي آمن، ثم يبث الاتصال محلياً عبر SOCKS5 و HTTP حتى يستطيع المستخدم توجيه أجهزته الأخرى (هواتف، متصفحات) عبره.

---

## الفرق عن التطبيق الحالي

| الجانب | الحالي (محلي) | SaaS (الجديد) |
|--------|---------------|---------------|
| مصدر البروكسيات | ملف `data.json` محلي | السيرفر المركزي عبر API |
| المصادقة | بدون حساب | JWT (Email + Password) |
| فحص البروكسيات | التطبيق يفحص مباشرة | السيرفر يفحص ويعطي الأفضل |
| رؤية IP البروكسي | المستخدم يرى كل شيء | لا يرى — يمر عبر Relay |
| الاستهلاك | غير محدود | محدود حسب الباقة |
| التحديثات | يدوي | Auto-updater |
| Ad Blocker | محلي | سيرفر + محلي (طبقتين) |
| الإعدادات | config.json محلي | مزامنة مع السيرفر |

---

## التقنية

| المكون | التقنية |
|--------|---------|
| Framework | Wails v2 |
| Backend | Go |
| Frontend | React + TypeScript |
| Styling | Tailwind CSS |
| Local Servers | SOCKS5 + HTTP Proxy (Go) |
| Auth | JWT (Access + Refresh) |
| Storage | SQLite محلي (cache + offline) |
| Auto-Update | go-selfupdate أو Sparkle |
| Build | GitHub Actions → Windows (.exe), macOS (.dmg), Linux (.AppImage) |
| Installer | NSIS (Windows), DMG (macOS) |

---

## الأنظمة المدعومة

| النظام | الحالة | الأولوية |
|--------|--------|----------|
| Windows 10/11 | ✅ مدعوم | 🔴 أولى |
| macOS 12+ | ✅ مدعوم | 🟡 ثانية |
| Linux (Ubuntu/Fedora) | ✅ مدعوم | 🟢 ثالثة |
| Android | 📱 مستقبلاً | ⚪ لاحقاً |
| iOS | 📱 مستقبلاً | ⚪ لاحقاً |

---

## مبادئ التصميم

1. **بسيط للغاية** — المستخدم يريد نقرة واحدة للاتصال
2. **Dark Theme** — متسق مع الموقع (`#0a0e17`)
3. **Frameless Window** — نافذة بدون إطار نظام (كالتطبيق الحالي)
4. **معلومات واضحة** — الاستهلاك، المنطقة، السرعة ظاهرة دائماً
5. **عدم كشف التعقيد** — المستخدم لا يحتاج يعرف عن Relay أو SOCKS5

---

## ميزة بث البروكسي (Proxy Broadcasting)

هذه هي الميزة الأساسية المميزة:

```
الكمبيوتر (التطبيق)              الهاتف / أجهزة أخرى
┌────────────────────┐           ┌──────────────────┐
│  Client App        │           │  📱 الهاتف       │
│  ┌──────────────┐  │    WiFi   │  يستخدم البروكسي │
│  │ SOCKS5 :1080 │◄─┼──────────┼── كـ System Proxy │
│  │ HTTP   :8080 │◄─┼──────────┤  أو SocksDroid   │
│  └──────┬───────┘  │           └──────────────────┘
│         │          │
│         │ TLS 1.3  │           ┌──────────────────┐
│         ▼          │           │  🖥️ كمبيوتر آخر │
│  ┌──────────────┐  │    LAN    │  يستخدم البروكسي │
│  │ Relay Server │◄─┼──────────┤  عبر Proxifier   │
│  └──────┬───────┘  │           └──────────────────┘
│         │          │
│         ▼          │
│  🌐 الإنترنت      │
└────────────────────┘
```

- التطبيق يفتح منافذ محلية (SOCKS5 + HTTP) على `0.0.0.0`
- أي جهاز على نفس الشبكة يمكنه الاتصال
- المصادقة: Whitelist تلقائي لـ `192.168.x.x` + اسم مستخدم/كلمة مرور
- الاستهلاك يُحسب على حساب المستخدم الواحد (كل الأجهزة)


---


<!-- ═══ client-app/SCREENS.md ═══ -->


# 📱 شاشات تطبيق العميل

---

## 1. شاشة التحميل (Splash Screen)

- لوغو المنتج في المنتصف مع animation (pulse أو fade)
- شريط تقدم صغير أسفل اللوغو
- خلفية: gradient داكن
- المدة: 1-3 ثواني (حتى يتم التحقق من الجلسة)
- السلوك: إذا JWT صالح → الشاشة الرئيسية | إذا لا → تسجيل الدخول

---

## 2. شاشة تسجيل الدخول (Login)

| العنصر | التفاصيل |
|--------|----------|
| اللوغو | في الأعلى |
| حقل Email | مع تحقق فوري |
| حقل Password | مع زر إظهار/إخفاء |
| Remember Me | خانة اختيار |
| زر "تسجيل الدخول" | Primary button |
| Forgot Password | رابط → يفتح المتصفح على صفحة الموقع |
| OAuth | "سجّل عبر Google" → يفتح المتصفح ويعود بـ token |
| رابط التسجيل | "ليس لديك حساب؟" → يفتح المتصفح على `/register` |

### السلوك
- عند النجاح: يحفظ JWT محلياً + ينتقل للشاشة الرئيسية
- عند الفشل: رسالة خطأ واضحة
- Device Fingerprint يُرسل مع طلب الدخول
- إذا تجاوز حد الأجهزة: رسالة "احذف جهاز من لوحة التحكم"

---

## 3. الشاشة الرئيسية (Main / Home)

### التقسيم

```
┌──────────────────────────────────────────┐
│  ─  □  ✕                    Proxy Redirector │  ← Title Bar (frameless)
├──────────────────────────────────────────┤
│                                          │
│         ┌──────────────────┐             │
│         │                  │             │
│         │   زر الاتصال     │             │
│         │  (دائرة كبيرة)   │             │
│         │                  │             │
│         └──────────────────┘             │
│                                          │
│     الحالة: 🟢 متصل  |  🔴 غير متصل     │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │  🌍 المنطقة: US - New York    [▼] │  │  ← Dropdown لاختيار المنطقة
│  │  ⚡ السرعة:  45ms                 │  │
│  │  📊 الاستهلاك: 12.5 / 200 GB     │  │
│  │  📱 الأجهزة:  3 متصلة            │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────┐ ┌────────┐ ┌────────┐       │
│  │الأجهزة │ │الإعدادات│ │ الحساب │       │  ← Tab bar سفلي
│  └────────┘ └────────┘ └────────┘       │
└──────────────────────────────────────────┘
```

### زر الاتصال
- **غير متصل**: دائرة رمادية مع أيقونة power — نص "اتصل"
- **جاري الاتصال**: animation دوران — نص "جاري الاتصال..."
- **متصل**: دائرة خضراء متوهجة (glow) — نص "متصل"
- **فشل**: دائرة حمراء — نص "فشل الاتصال — اضغط لإعادة المحاولة"

### اختيار المنطقة
- Dropdown يعرض: اسم المنطقة + العلم + عدد الخوادم + Ping تقريبي
- مناطق مقفلة (حسب الباقة) تظهر بشكل باهت مع 🔒
- "أفضل موقع" كخيار أول (Auto) — يختار الأقل ping

### شريط الاستهلاك
- Progress bar ملون: أخضر < 50% | أصفر 50-80% | أحمر > 80%
- عند الضغط: يفتح تفاصيل الاستهلاك اليومي

---

## 4. شاشة الأجهزة المتصلة (Connected Devices)

| العنصر | التفاصيل |
|--------|----------|
| عنوان | "الأجهزة المتصلة عبر شبكتك" |
| قائمة | كل جهاز: IP + اسم (إذا معروف) + البروتوكول (SOCKS5/HTTP) + الهدف الحالي |
| عداد | "3 أجهزة متصلة الآن" |
| معلومات البث | عنوان IP المحلي + المنافذ (SOCKS5: 1080, HTTP: 8080) |
| QR Code | يولّد QR code لإعدادات البروكسي — الهاتف يمسحه ويُعدّ تلقائياً |
| نسخ الإعدادات | زر نسخ: `192.168.1.100:8080` |

### أفكار إضافية
- دليل إعداد سريع لكل نظام (Android, iOS, PC) — 3 خطوات مع صور
- زر "اختبر الاتصال" — يفحص هل الجهاز يمر عبر البروكسي

---

## 5. شاشة الإعدادات (Settings)

| القسم | العناصر |
|-------|---------|
| **الاتصال** | المنافذ (SOCKS5, HTTP) — تغيير يحتاج إعادة تشغيل |
| **المصادقة المحلية** | تشغيل/إيقاف — اسم المستخدم وكلمة المرور للأجهزة |
| **Ad Blocker** | تشغيل/إيقاف حجب الإعلانات |
| **بدء تلقائي** | تشغيل التطبيق مع Windows |
| **بدء متصل** | الاتصال تلقائياً عند فتح التطبيق |
| **System Tray** | تصغير للـ Tray عند الإغلاق |
| **المظهر** | داكن / فاتح / تلقائي (يتبع النظام) |
| **اللغة** | عربي / إنجليزي |
| **حول** | رقم الإصدار + التحقق من تحديثات |
| **تسجيل خروج** | زر تسجيل خروج مع تأكيد |

---

## 6. شاشة الحساب (Account)

| العنصر | التفاصيل |
|--------|----------|
| البريد | email المستخدم |
| الخطة | اسم الباقة + تاريخ التجديد |
| الاستهلاك | رسم بياني مصغر لآخر 7 أيام |
| الأجهزة المسجلة | قائمة الأجهزة (من السيرفر) مع زر حذف |
| ترقية | زر "ترقية الباقة" → يفتح الموقع |
| إدارة الحساب | "إدارة حسابك" → يفتح Dashboard في المتصفح |

---

## 7. System Tray (أيقونة شريط المهام)

عند تصغير التطبيق:

| الإجراء | السلوك |
|---------|--------|
| Right-click | قائمة: اتصال/قطع — المنطقة — فتح التطبيق — خروج |
| Left-click | فتح/إخفاء النافذة |
| الأيقونة | تتغير حسب الحالة: رمادي (غير متصل) / أخضر (متصل) / أحمر (خطأ) |
| Tooltip | "Proxy Redirector — متصل (US) — 12.5GB مستخدم" |

---

## 8. الإشعارات (Notifications)

| الحدث | نوع الإشعار | المحتوى |
|-------|------------|---------|
| اتصال ناجح | Toast (أخضر) | "✅ متصل بـ US - New York" |
| فشل اتصال | Toast (أحمر) | "❌ فشل الاتصال — جاري المحاولة..." |
| تبديل بروكسي | Toast (أزرق) | "🔄 تم التبديل لخادم أسرع" |
| 80% استهلاك | System Notification | "⚠️ استخدمت 80% من باندويثك" |
| 100% استهلاك | Modal داخلي | "انتهى الباندويث — ترقية أو انتظر التجديد" |
| تحديث متاح | Modal داخلي | "إصدار جديد متاح — تحديث الآن؟" |
| جهاز جديد متصل | Toast (أزرق) | "📱 جهاز جديد اتصل: 192.168.1.50" |

---

## 9. شاشة التحديث (Update)

- تظهر عند توفر إصدار جديد
- تعرض: رقم الإصدار الجديد + ملخص التغييرات
- زرين: "تحديث الآن" + "لاحقاً"
- شريط تقدم أثناء التنزيل
- بعد التنزيل: "إعادة تشغيل لتطبيق التحديث"

---

## 10. حالات خاصة

### أول استخدام (Onboarding)
- 3 شاشات سريعة: الميزات → اختيار المنطقة → اتصل
- زر "تخطي" متاح

### لا يوجد إنترنت
- رسالة واضحة مع أيقونة
- زر "إعادة المحاولة"
- إذا كان متصلاً سابقاً: يحاول إعادة الاتصال تلقائياً

### الباقة انتهت
- Modal: "انتهت باقتك — ترقية أو استخدم الخطة المجانية"
- إذا Free: يعمل بسرعة محدودة + 500MB


---



================================================================================

# ☁️ السيرفر والبنية التحتية (Server)

================================================================================



<!-- ═══ server/API_SPEC.md ═══ -->


# 🔌 مواصفات API كاملة

---

## القواعد العامة

| القاعدة | التفاصيل |
|---------|----------|
| Base URL | `https://api.proxyredirector.com/api/v1` |
| Content-Type | `application/json` |
| Auth Header | `Authorization: Bearer <access_token>` |
| Rate Limit | 60 req/min (عام) — 10 req/min (auth endpoints) |
| Pagination | `?page=1&per_page=20` |
| Errors | `{ "error": "message", "code": "ERROR_CODE" }` |
| Timestamps | ISO 8601 (UTC) |

---

## 1. المصادقة (Auth)

### `POST /auth/register`
**بدون Auth**

| المدخل | النوع | مطلوب | وصف |
|--------|-------|-------|-----|
| email | string | ✅ | بريد إلكتروني صالح |
| password | string | ✅ | 8 أحرف على الأقل |

**الرد (201):**
```json
{
  "user": { "id": "uuid", "email": "user@example.com", "role": "client" },
  "message": "تحقق من بريدك لتأكيد الحساب"
}
```

**الأخطاء:** `EMAIL_EXISTS`, `WEAK_PASSWORD`, `INVALID_EMAIL`

---

### `POST /auth/login`
**بدون Auth**

| المدخل | النوع | مطلوب | وصف |
|--------|-------|-------|-----|
| email | string | ✅ | |
| password | string | ✅ | |
| device_fingerprint | string | ✅ | hash الجهاز |
| device_name | string | ❌ | "Hassan's PC" |
| device_os | string | ❌ | "Windows 11" |

**الرد (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "client",
    "plan": "pro",
    "bandwidth_remaining_gb": 187.5
  }
}
```

**الأخطاء:** `INVALID_CREDENTIALS`, `EMAIL_NOT_VERIFIED`, `ACCOUNT_BANNED`, `DEVICE_LIMIT_REACHED`

---

### `POST /auth/refresh`
| المدخل | النوع | وصف |
|--------|-------|-----|
| refresh_token | string | Refresh token |

**الرد:** نفس رد login (access_token + refresh_token جديدين)

---

### `POST /auth/logout`
**Auth مطلوب**

يُبطل Access Token الحالي + Refresh Token.

---

### `POST /auth/forgot-password`
| المدخل | النوع | وصف |
|--------|-------|-----|
| email | string | البريد المسجّل |

يرسل رابط إعادة تعيين عبر البريد. يرد دائماً بـ 200 (لا يكشف هل البريد مسجّل).

---

### `POST /auth/reset-password`
| المدخل | النوع | وصف |
|--------|-------|-----|
| token | string | Token من رابط البريد |
| password | string | كلمة المرور الجديدة |

---

### `GET /auth/verify-email?token=xxx`
يؤكد البريد ويُفعّل الحساب.

---

## 2. البروكسي (Proxy)

### `POST /proxy/connect`
**Auth مطلوب**

| المدخل | النوع | مطلوب | وصف |
|--------|-------|-------|-----|
| region | string | ❌ | كود المنطقة ("US", "EU") — فارغ = auto |
| protocol | string | ❌ | "socks5" أو "http" — افتراضي: socks5 |

**الرد (200):**
```json
{
  "session_id": "uuid",
  "relay": {
    "host": "us-east.relay.proxyredirector.com",
    "port": 443,
    "session_token": "encrypted_token",
    "expires_at": "2026-06-28T15:00:00Z"
  },
  "region": "US",
  "protocol": "socks5"
}
```

**الأخطاء:** `NO_BANDWIDTH`, `REGION_NOT_ALLOWED`, `NO_RELAY_AVAILABLE`, `PLAN_EXPIRED`

**المنطق الداخلي:**
1. التحقق من الباقة والباندويث
2. اختيار أفضل Relay Server (الأقل حملاً في المنطقة)
3. إنشاء Session في DB
4. توليد session_token مشفر (يحتوي user_id + session_id + expiry)
5. إرسال البيانات للتطبيق

---

### `POST /proxy/disconnect`
**Auth مطلوب**

| المدخل | النوع | وصف |
|--------|-------|-----|
| session_id | string | UUID الجلسة |

يُغلق الجلسة ويحفظ إجمالي الاستهلاك.

---

### `GET /proxy/regions`
**Auth مطلوب**

**الرد:**
```json
{
  "regions": [
    {
      "code": "US",
      "name": "United States",
      "cities": ["New York", "Los Angeles"],
      "servers": 3,
      "load_pct": 45,
      "avg_latency_ms": 120,
      "available": true
    },
    {
      "code": "DE",
      "name": "Germany",
      "available": false,
      "locked_reason": "PLAN_UPGRADE_REQUIRED"
    }
  ]
}
```

---

## 3. المستخدم (User)

### `GET /user/profile`
**Auth مطلوب**

**الرد:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "client",
  "created_at": "2026-01-15T10:00:00Z",
  "plan": {
    "name": "pro",
    "bandwidth_gb": 200,
    "max_devices": 5,
    "max_regions": -1
  },
  "subscription": {
    "status": "active",
    "current_period_end": "2026-07-28T00:00:00Z",
    "bandwidth_used_gb": 12.5,
    "bandwidth_remaining_gb": 187.5
  }
}
```

---

### `GET /user/usage`
**Auth مطلوب**

Query params: `?period=30d` (7d, 30d, 90d)

**الرد:**
```json
{
  "current_period": {
    "bandwidth_used_gb": 12.5,
    "bandwidth_limit_gb": 200,
    "percentage": 6.25
  },
  "daily": [
    { "date": "2026-06-28", "bytes_up": 104857600, "bytes_down": 524288000 },
    { "date": "2026-06-27", "bytes_up": 209715200, "bytes_down": 1073741824 }
  ]
}
```

---

### `POST /user/usage/report`
**Auth مطلوب** — يُستدعى من التطبيق كل 30 ثانية

| المدخل | النوع | وصف |
|--------|-------|-----|
| session_id | string | UUID الجلسة |
| bytes_up | integer | بايتات مرسلة |
| bytes_down | integer | بايتات مستقبلة |
| interval_seconds | integer | الفترة الزمنية |

**الرد:**
```json
{
  "status": "ok",
  "bandwidth_remaining_gb": 187.2,
  "action": "none"
}
```

**القيم الممكنة لـ action:** `none`, `warning`, `throttle`, `disconnect`

---

### `GET /user/devices`
**Auth مطلوب**

**الرد:**
```json
{
  "devices": [
    {
      "id": "uuid",
      "name": "Hassan's PC",
      "os": "Windows 11",
      "last_active": "2026-06-28T12:00:00Z",
      "is_current": true
    }
  ],
  "limit": 5,
  "count": 3
}
```

---

### `DELETE /user/devices/{id}`
**Auth مطلوب** — يحذف جهاز ويُبطل جلساته.

---

## 4. الاشتراكات (Subscription)

### `GET /subscription/current`
**Auth مطلوب** — تفاصيل الاشتراك الحالي.

### `POST /subscription/upgrade`
| المدخل | النوع | وصف |
|--------|-------|-----|
| plan_id | string | UUID الخطة الجديدة |

يُنشئ Stripe Checkout Session ويرد بـ URL.

---

## 5. الفوترة (Billing)

### `GET /billing/plans`
**بدون Auth** — الخطط المتاحة مع الأسعار.

### `POST /billing/checkout`
**Auth مطلوب**

| المدخل | النوع | وصف |
|--------|-------|-----|
| plan_id | string | UUID الخطة |
| interval | string | "monthly" أو "yearly" |

**الرد:** `{ "checkout_url": "https://checkout.stripe.com/..." }`

### `POST /billing/webhook`
**بدون Auth** — يتحقق من Stripe signature.
يعالج أحداث: `checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`

### `GET /billing/invoices`
**Auth مطلوب** — قائمة الفواتير مع رابط PDF.

### `POST /billing/cancel`
**Auth مطلوب** — يُلغي الاشتراك (يبقى فعالاً حتى نهاية الفترة).

---

## 6. الإدارة (Admin)

> كل endpoints الإدارة تتطلب `role: admin` أو `super_admin`

### `GET /admin/users`
Query: `?page=1&per_page=20&search=email&status=active&plan=pro`

### `GET /admin/users/{id}`
تفاصيل مستخدم مع الاشتراك + الأجهزة + الاستهلاك.

### `PATCH /admin/users/{id}`
تعديل: role, status, bandwidth_limit.

### `POST /admin/users/{id}/ban`
حظر المستخدم + إبطال كل جلساته.

### `GET /admin/proxies`
Query: `?status=active&country=US&page=1`

### `POST /admin/proxies/import`
Content-Type: `multipart/form-data` — ملف JSON/CSV/TXT.

### `GET /admin/relays`
حالة كل Relay Server: load, connections, uptime, last_heartbeat.

### `GET /admin/analytics/overview`
```json
{
  "mau": 450,
  "active_connections": 128,
  "total_bandwidth_today_gb": 340,
  "mrr_cents": 215000,
  "new_users_today": 12,
  "churn_rate_pct": 5.2
}
```

### `GET /admin/analytics/revenue`
Query: `?period=30d` — تقرير إيرادات مفصّل.

### `GET /admin/audit`
Query: `?actor_id=uuid&action=user.login&page=1`
سجل العمليات الحساسة.

---

## 7. التطبيق (App)

### `GET /app/version`
**بدون Auth**

```json
{
  "latest": "2.1.0",
  "min_supported": "2.0.0",
  "download": {
    "windows": "https://...",
    "macos": "https://...",
    "linux": "https://..."
  },
  "changelog": "- إصلاح مشكلة الاتصال\n- تحسين السرعة"
}
```

---

## أكواد الأخطاء

| Code | HTTP | وصف |
|------|------|-----|
| `INVALID_CREDENTIALS` | 401 | بيانات دخول خاطئة |
| `TOKEN_EXPIRED` | 401 | JWT منتهي |
| `TOKEN_INVALID` | 401 | JWT غير صالح |
| `FORBIDDEN` | 403 | لا يملك صلاحية |
| `EMAIL_EXISTS` | 409 | البريد مسجّل مسبقاً |
| `EMAIL_NOT_VERIFIED` | 403 | لم يتم تأكيد البريد |
| `ACCOUNT_BANNED` | 403 | الحساب محظور |
| `DEVICE_LIMIT_REACHED` | 403 | تجاوز حد الأجهزة |
| `NO_BANDWIDTH` | 403 | انتهى الباندويث |
| `PLAN_EXPIRED` | 403 | الاشتراك منتهي |
| `REGION_NOT_ALLOWED` | 403 | المنطقة غير متاحة في الباقة |
| `NO_RELAY_AVAILABLE` | 503 | لا يوجد relay server متاح |
| `RATE_LIMITED` | 429 | تجاوز حد الطلبات |
| `NOT_FOUND` | 404 | المورد غير موجود |
| `VALIDATION_ERROR` | 422 | بيانات غير صالحة |


---


<!-- ═══ server/DEPLOYMENT.md ═══ -->


# 🚀 خطة النشر والتوزيع (Deployment)

---

## 1. Central API

### الاستضافة: Railway أو Fly.io

| العنصر | التفاصيل |
|--------|----------|
| Container | Docker (Dockerfile.api) |
| Port | 8000 |
| Domain | `api.proxyredirector.com` |
| SSL | تلقائي (Let's Encrypt) |
| Scaling | Horizontal (2-4 instances) |
| Health Check | `GET /health` |

### CI/CD (GitHub Actions)
```
Push to main:
  → Run tests (go test ./...)
  → Build Docker image
  → Push to container registry
  → Deploy to Railway (auto)
  → Run migrations (post-deploy hook)
```

---

## 2. Relay Servers

### الاستضافة: VPS مستقلة

| المنطقة | المزود | المواصفات | الـ IP |
|---------|--------|-----------|--------|
| US-East | DigitalOcean (NYC) | 2 vCPU, 4GB, 4TB transfer | ثابت |
| EU-West | Hetzner (Amsterdam) | 2 vCPU, 4GB, 20TB transfer | ثابت |
| Asia | DigitalOcean (Singapore) | 2 vCPU, 4GB, 4TB transfer | ثابت |
| ME | Hetzner (Falkenstein) | 2 vCPU, 4GB, 20TB transfer | ثابت |

### النشر على كل VPS
```
1. SSH إلى VPS
2. Docker pull relay:latest
3. docker-compose up -d
4. التحقق: curl http://localhost:50051/health
```

### أو عبر GitHub Actions
```
Push tag (relay-v*):
  → Build Dockerfile.relay
  → SSH deploy to all relay VPS
  → Health check each server
  → Update Central API with new relay versions
```

### DNS
```
us-east.relay.proxyredirector.com  →  VPS IP (US)
eu-west.relay.proxyredirector.com  →  VPS IP (EU)
asia.relay.proxyredirector.com     →  VPS IP (Asia)
me.relay.proxyredirector.com       →  VPS IP (ME)
```

---

## 3. Database (PostgreSQL)

### الاستضافة: Supabase

| العنصر | التفاصيل |
|--------|----------|
| Plan | Pro ($25/mo) |
| Region | US-East (أقرب لـ API) |
| Connection | Connection pooling (PgBouncer) |
| Backups | يومية تلقائية (7 أيام) |
| Migrations | GORM AutoMigrate أو golang-migrate |

### إعداد أولي
1. إنشاء مشروع Supabase
2. تشغيل migrations
3. Seed: إنشاء الخطط + حساب Super Admin
4. تفعيل RLS (Row Level Security) إذا مطلوب

---

## 4. Redis

### الاستضافة: Upstash

| العنصر | التفاصيل |
|--------|----------|
| Plan | Pay-per-use (أول 10K commands مجاني) |
| Region | US-East |
| الاستخدام | JWT blacklist, rate limits, session cache |
| TTL | Access tokens: 15 دقيقة, Rate limits: 1 دقيقة |

---

## 5. Website (Admin + Marketing)

### الاستضافة: Vercel

| العنصر | التفاصيل |
|--------|----------|
| Framework | Next.js 14 |
| Domain | `proxyredirector.com` |
| Build | `next build` (automatic on push) |
| Environment | `.env.local` → Vercel Environment Variables |

---

## 6. Client App Distribution

### التوزيع عبر GitHub Releases

| النظام | الملف | الحجم المتوقع |
|--------|-------|---------------|
| Windows | `ProxyRedirector-Setup-2.0.0.exe` | ~15MB |
| macOS | `ProxyRedirector-2.0.0.dmg` | ~20MB |
| Linux | `ProxyRedirector-2.0.0.AppImage` | ~18MB |

### CI/CD
```
Push tag (v*):
  → Wails build (Windows, macOS, Linux)
  → Code signing (Windows: signtool, macOS: codesign)
  → Upload to GitHub Release
  → Update /api/v1/app/version endpoint
  → Update download links on website
```

### التوزيع البديل
- **Website**: صفحة `/download` تكتشف النظام وتعرض الزر المناسب
- **S3/Cloudflare R2**: للتنزيل السريع (CDN)
- **Microsoft Store / Homebrew**: مستقبلاً

---

## 7. Docker Compose (Development)

```yaml
# docker-compose.yml (تطوير محلي)
services:
  api:
    build: ./deployments/docker/Dockerfile.api
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis]

  relay:
    build: ./deployments/docker/Dockerfile.relay
    ports: ["443:443", "50051:50051"]
    env_file: .env

  worker:
    build: ./deployments/docker/Dockerfile.worker
    env_file: .env
    depends_on: [postgres, redis]

  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: proxy_saas
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: devpassword
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pgdata:
```

---

## 8. المراقبة (Monitoring)

| الأداة | الغرض |
|--------|-------|
| Prometheus | جمع Metrics (requests, latency, errors) |
| Grafana | لوحات مراقبة مرئية |
| Sentry | تتبع الأخطاء (Error tracking) |
| UptimeRobot | مراقبة Uptime + تنبيهات |
| Logflare/Betterstack | Centralized logging |

### Metrics المطلوبة
- API: requests/sec, response time (p50, p95, p99), error rate
- Relay: active connections, bandwidth throughput, tunnel errors
- DB: query time, connection pool usage
- Business: active users, new signups, revenue


---


<!-- ═══ server/FILE_STRUCTURE.md ═══ -->


# 📁 هيكلية ملفات السيرفر

```
server/
├── cmd/
│   ├── api/
│   │   └── main.go                 # Entry point: Central API server
│   ├── relay/
│   │   └── main.go                 # Entry point: Relay server binary
│   └── worker/
│       └── main.go                 # Entry point: Background health worker
│
├── internal/
│   ├── config/
│   │   └── config.go               # تحميل ENV + validation
│   │
│   ├── database/
│   │   ├── database.go             # اتصال PostgreSQL (GORM)
│   │   ├── redis.go                # اتصال Redis
│   │   └── migrations/
│   │       ├── 001_create_users.go
│   │       ├── 002_create_plans.go
│   │       ├── 003_create_subscriptions.go
│   │       ├── 004_create_devices.go
│   │       ├── 005_create_proxies.go
│   │       ├── 006_create_relay_servers.go
│   │       ├── 007_create_sessions.go
│   │       ├── 008_create_usage_logs.go
│   │       └── 009_create_audit_logs.go
│   │
│   ├── models/                     # GORM models
│   │   ├── user.go
│   │   ├── plan.go
│   │   ├── subscription.go
│   │   ├── device.go
│   │   ├── proxy.go
│   │   ├── relay_server.go
│   │   ├── session.go
│   │   ├── usage_log.go
│   │   └── audit_log.go
│   │
│   ├── handlers/                   # HTTP handlers (Fiber)
│   │   ├── auth_handler.go         # register, login, refresh, logout, etc.
│   │   ├── proxy_handler.go        # connect, disconnect, regions
│   │   ├── user_handler.go         # profile, usage, devices
│   │   ├── billing_handler.go      # plans, checkout, webhook, invoices
│   │   ├── admin_handler.go        # users, proxies, relays, analytics
│   │   └── app_handler.go          # version check
│   │
│   ├── services/                   # Business logic
│   │   ├── auth_service.go         # JWT creation/validation, password hashing
│   │   ├── proxy_service.go        # Relay selection, session management
│   │   ├── user_service.go         # CRUD, device management
│   │   ├── billing_service.go      # Stripe integration, plan management
│   │   ├── usage_service.go        # Bandwidth tracking, quota enforcement
│   │   ├── relay_service.go        # Relay health, load balancing
│   │   ├── email_service.go        # Transactional emails (Resend)
│   │   └── audit_service.go        # Audit logging
│   │
│   ├── middleware/
│   │   ├── auth.go                 # JWT verification middleware
│   │   ├── rbac.go                 # Role-based access control
│   │   ├── rate_limit.go           # Redis-based rate limiting
│   │   ├── cors.go                 # CORS configuration
│   │   └── logger.go               # Request logging
│   │
│   ├── router/
│   │   └── router.go               # Route registration
│   │
│   ├── relay/                      # Relay Server logic
│   │   ├── server.go               # TLS listener + client handler
│   │   ├── tunnel.go               # Tunnel management (client ↔ proxy)
│   │   ├── auth.go                 # Session token validation (via gRPC)
│   │   ├── proxy_pool.go           # Local proxy pool management
│   │   └── health.go               # Self-reporting to Central API
│   │
│   ├── worker/                     # Background workers
│   │   ├── proxy_checker.go        # Periodic proxy health checking
│   │   ├── usage_aggregator.go     # Usage log aggregation
│   │   ├── subscription_expiry.go  # Expired subscription handler
│   │   └── relay_monitor.go        # Relay server health monitor
│   │
│   ├── grpc/                       # gRPC (Relay ↔ API)
│   │   ├── proto/
│   │   │   └── relay.proto         # Protocol buffer definitions
│   │   ├── server.go               # gRPC server (in Central API)
│   │   └── client.go               # gRPC client (in Relay Server)
│   │
│   └── pkg/                        # Shared utilities
│       ├── jwt.go                  # JWT helpers
│       ├── hash.go                 # Password hashing (bcrypt)
│       ├── validator.go            # Input validation
│       ├── crypto.go               # Encryption helpers
│       ├── response.go             # Standard API response format
│       └── errors.go               # Error codes
│
├── deployments/
│   ├── docker/
│   │   ├── Dockerfile.api          # Central API image
│   │   ├── Dockerfile.relay        # Relay Server image
│   │   └── Dockerfile.worker       # Worker image
│   ├── docker-compose.yml          # Local development stack
│   ├── docker-compose.prod.yml     # Production overrides
│   └── nginx/
│       └── nginx.conf              # Reverse proxy config
│
├── scripts/
│   ├── seed.go                     # Seed database (plans, admin user)
│   ├── migrate.go                  # Run migrations
│   └── import_proxies.go           # Bulk import proxies
│
├── keys/                           # JWT keys (gitignored)
│   ├── private.pem
│   └── public.pem
│
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + Test
│       ├── deploy-api.yml          # Deploy Central API
│       └── deploy-relay.yml        # Deploy Relay Servers
│
├── go.mod
├── go.sum
├── Makefile
├── .env.example
└── README.md
```

---

## ملاحظات على الهيكلية

- **`cmd/`**: كل binary مستقل (API, Relay, Worker)
- **`internal/`**: لا يمكن استيرادها من خارج المشروع (Go convention)
- **`handlers/`** → **`services/`** → **`models/`**: فصل واضح بين الطبقات
- **`relay/`**: يعمل كـ binary مستقل على VPS منفصلة
- **`worker/`**: cron jobs تعمل بشكل مستقل أو داخل API


---


<!-- ═══ server/OVERVIEW.md ═══ -->


# ☁️ السيرفر والبنية التحتية — نظرة عامة

## الغرض

البنية الخلفية الكاملة التي تدير نظام Proxy Redirector SaaS:
- **Central API**: المصادقة، إدارة المستخدمين، تعيين البروكسيات، تتبع الاستهلاك
- **Relay Servers**: خوادم وسيطة تُمرر حركة المستخدمين للبروكسيات
- **Proxy Health Worker**: فحص دوري لصحة البروكسيات
- **Admin Dashboard Backend**: APIs لإدارة النظام

---

## المكونات

```
┌─────────────────────────────────────────────────────────┐
│                    Central API (Go)                       │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ Auth     │ │ Proxy    │ │ Billing  │ │ Admin      │ │
│  │ Module   │ │ Module   │ │ Module   │ │ Module     │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Usage    │ │ Device   │ │ Audit    │               │
│  │ Module   │ │ Module   │ │ Module   │               │
│  └──────────┘ └──────────┘ └──────────┘               │
└───────────────────────┬─────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
   ┌──────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
   │ PostgreSQL  │ │ Redis  │ │ Relay      │
   │ (Supabase)  │ │        │ │ Servers    │
   └─────────────┘ └────────┘ │ (Multi-VPS)│
                               └────────────┘
```

---

## التقنية

| المكون | التقنية | السبب |
|--------|---------|-------|
| Language | Go 1.22+ | أداء عالي، binary واحد، concurrency |
| HTTP Framework | Fiber v2 | سريع، Express-like API |
| ORM | GORM | migrations + query builder |
| Database | PostgreSQL 16 (Supabase) | JSONB, partitioning, RLS |
| Cache | Redis 7 (Upstash) | Sessions, rate limits, pub/sub |
| Auth | JWT (RS256) | Stateless + refresh tokens |
| Relay Protocol | TLS 1.3 + custom handshake | أمان + أداء |
| Internal RPC | gRPC | Relay ↔ API اتصال داخلي |
| Payments | Stripe API | Checkout, subscriptions, webhooks |
| Email | Resend API | Transactional emails |
| Logging | zerolog | Structured JSON logging |
| Monitoring | Prometheus + Grafana | Metrics + dashboards |
| Deployment | Docker + Docker Compose | Reproducible environments |

---

## البيئات

| البيئة | الغرض | URL |
|--------|-------|-----|
| Development | تطوير محلي | `localhost:8000` |
| Staging | اختبار قبل الإنتاج | `api-staging.proxyredirector.com` |
| Production | الإنتاج | `api.proxyredirector.com` |

---

## Environment Variables المطلوبة

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/proxy_saas

# Redis
REDIS_URL=redis://default:pass@host:6379

# JWT
JWT_PRIVATE_KEY_PATH=./keys/private.pem
JWT_PUBLIC_KEY_PATH=./keys/public.pem
JWT_ACCESS_TTL=15m
JWT_REFRESH_TTL=7d

# Stripe
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Email
RESEND_API_KEY=re_xxx
FROM_EMAIL=noreply@proxyredirector.com

# Relay
RELAY_AUTH_SECRET=shared_secret_for_relay_servers
RELAY_GRPC_PORT=50051

# App
APP_ENV=production
APP_PORT=8000
CORS_ORIGINS=https://proxyredirector.com
```


---


<!-- ═══ server/PROXY_SOURCES.md ═══ -->


# 🌐 مصادر البروكسيات وإدارتها

---

## 1. مصادر البروكسيات

### أ. المصادر المجانية (Scraping)

| المصدر | النوع | الجودة | الكمية |
|--------|-------|--------|--------|
| قوائم عامة (free-proxy-list.net, etc.) | HTTP/SOCKS | منخفضة | آلاف |
| GitHub repos (proxy lists) | مختلط | منخفضة-متوسطة | مئات |
| Scraping مخصص | مختلط | متوسطة | حسب الجهد |

**المشاكل:** غير مستقرة، بطيئة، تُكشف بسرعة، لا SLA.
**الاستخدام:** خطة Free فقط أو كاحتياطي.

### ب. المصادر المدفوعة (Premium Pools)

| المزود | النوع | السعر التقريبي | الميزة |
|--------|-------|----------------|--------|
| Bright Data | Residential/DC | $500+/mo | أكبر شبكة، 72M+ IPs |
| Oxylabs | Residential/DC | $300+/mo | موثوق، API جيد |
| IPRoyal | Residential | $50+/mo | رخيص، API بسيط |
| Webshare | Datacenter | $30+/mo | رخيص جداً، DC فقط |
| ProxyScrape | مختلط | $50+/mo | API + قوائم |
| Smartproxy | Residential | $80+/mo | سهل الاستخدام |

**التوصية للبداية:** Webshare (DC) + IPRoyal (Residential) = ~$80-130/شهر

### ج. البروكسيات الخاصة (Self-Hosted)

- شراء VPS رخيصة في مناطق مختلفة
- تثبيت Squid أو 3proxy أو Dante
- تكلفة: $3-5/VPS/شهر
- ميزة: تحكم كامل + موثوقية عالية
- عيب: عدد محدود + تحتاج إدارة

---

## 2. آلية إدارة البروكسيات

### دورة حياة البروكسي

```
[استيراد] → [في الانتظار] → [فحص] → [نشط] ←→ [ميت مؤقت]
                                          ↓              ↓
                                    [مُعيّن لعميل]   [إعادة فحص]
                                          ↓              ↓
                                    [مستخدم]       [نشط] أو [محظور نهائياً]
```

### حالات البروكسي

| الحالة | الوصف | الإجراء |
|--------|-------|---------|
| `pending` | تم استيراده، لم يُفحص بعد | ينتظر دوره في الفحص |
| `checking` | قيد الفحص الآن | لا يُعيّن لأحد |
| `active` | يعمل، متاح للتعيين | يمكن تعيينه لعميل |
| `assigned` | مُعيّن لجلسة نشطة | لا يُعيّن لعميل آخر (Dedicated) |
| `dead` | فشل في آخر فحص | ينتظر إعادة فحص |
| `blacklisted` | فشل متكرر (15+ مرة) | لا يُفحص مجدداً |

### الفحص الدوري (Health Worker)

```
كل 60 ثانية:
  1. اختيار batch من البروكسيات (الأقدم فحصاً أولاً)
  2. فحص كل بروكسي: HTTP request عبر البروكسي → httpbin.org/ip
  3. تسجيل: alive/dead + response_time_ms + IP المُرجع
  4. تحديث الحالة في DB
  5. تحديث reliability_score

كل 5 دقائق:
  - إعادة فحص البروكسيات الميتة (فرصة ثانية)
  - الأقل فشلاً أولاً

كل ساعة:
  - فحص شامل لكل البروكسيات النشطة
  - تحديث إحصائيات البلدان
```

---

## 3. استيراد البروكسيات

### التنسيقات المدعومة

**JSON:**
```json
[
  { "ip": "1.2.3.4", "port": 8080, "type": "socks5", "country": "US" }
]
```

**CSV:**
```
ip,port,type,country
1.2.3.4,8080,socks5,US
```

**TXT (سطر واحد لكل بروكسي):**
```
socks5://1.2.3.4:8080
http://5.6.7.8:3128
1.2.3.4:8080:socks5
```

### عملية الاستيراد
1. Admin يرفع الملف عبر API أو Dashboard
2. النظام يُحلل التنسيق ويُوحّده
3. يُزيل التكرارات (حسب IP:Port)
4. يُضيف بحالة `pending`
5. Worker يبدأ فحصها تلقائياً

---

## 4. تعيين البروكسي للعميل

### خوارزمية الاختيار

```
عند طلب POST /proxy/connect:

1. فلترة حسب المنطقة المطلوبة
2. فلترة: status = 'active' فقط
3. ترتيب حسب:
   - reliability_score (الأعلى أولاً) — وزن 40%
   - speed_ms (الأقل أولاً) — وزن 30%
   - last_assigned (الأقدم أولاً) — وزن 20%  ← توزيع متساوي
   - current_load (الأقل أولاً) — وزن 10%
4. اختيار أفضل Relay Server في المنطقة
5. تعيين البروكسي للـ Relay
6. إنشاء Session
```

### التوزيع
- **Shared Mode (افتراضي):** عدة عملاء يمكن أن يُعيّنوا لنفس البروكسي عبر relay مختلفة
- **Dedicated Mode (Business+):** البروكسي يُقفل لعميل واحد فقط

---

## 5. مراقبة جودة البروكسيات

### المقاييس المُتتبعة لكل بروكسي

| المقياس | الوصف |
|---------|-------|
| uptime_pct | نسبة الوقت الذي كان فيه حياً |
| avg_speed_ms | متوسط زمن الاستجابة |
| reliability_score | 0-100 (مركب) |
| total_checks | عدد مرات الفحص |
| consecutive_failures | عدد الفشل المتتالي |
| last_checked | آخر فحص |
| country | البلد (يُتحقق منه دورياً) |
| anonymity | transparent / anonymous / elite |

### التنبيهات

| الحدث | التنبيه |
|-------|---------|
| نسبة البروكسيات النشطة < 50% | ⚠️ تحذير للـ Admin |
| لا يوجد بروكسي نشط في منطقة | 🔴 تنبيه عاجل |
| بروكسي يسرّب IP حقيقي | 🔴 حظر فوري + تنبيه |
| مزود بروكسيات أوقف الخدمة | ⚠️ تنبيه + تفعيل المصدر البديل |


---


<!-- ═══ server/SCALING.md ═══ -->


# 📈 خطة التوسع والمراقبة (Scaling)

---

## 1. مراحل التوسع

### المرحلة 1: الإطلاق (0 - 100 مستخدم)

| المكون | المواصفات | التكلفة |
|--------|-----------|---------|
| API | Railway (1 instance) | $20/mo |
| DB | Supabase Free/Pro | $0-25/mo |
| Redis | Upstash Free | $0/mo |
| Relay | 2 VPS (US + EU) | $30/mo |
| **المجموع** | | **~$50-75/mo** |

**لا نحتاج:**
- Load balancer
- Multiple API instances
- CDN
- Monitoring متقدم

---

### المرحلة 2: النمو (100 - 1,000 مستخدم)

| المكون | المواصفات | التكلفة |
|--------|-----------|---------|
| API | Railway (2 instances) | $40/mo |
| DB | Supabase Pro | $25/mo |
| Redis | Upstash Pay-as-you-go | $10/mo |
| Relay | 4 VPS (US, EU, Asia, ME) | $60/mo |
| CDN | Cloudflare (Free) | $0/mo |
| Monitoring | UptimeRobot + Sentry Free | $0/mo |
| **المجموع** | | **~$135/mo** |

**نحتاج:**
- تفعيل Connection Pooling (PgBouncer)
- Rate limiting أكثر صرامة
- Monitoring أساسي

---

### المرحلة 3: التوسع (1,000 - 10,000 مستخدم)

| المكون | المواصفات | التكلفة |
|--------|-----------|---------|
| API | Fly.io (4+ instances, multi-region) | $100/mo |
| DB | Supabase Pro + Read Replicas | $75/mo |
| Redis | Upstash Pro | $30/mo |
| Relay | 8+ VPS (multi-region) | $200/mo |
| CDN | Cloudflare Pro | $20/mo |
| Monitoring | Grafana Cloud + Sentry Pro | $50/mo |
| Email | Resend Pro | $20/mo |
| **المجموع** | | **~$500/mo** |

**نحتاج:**
- Database read replicas
- API multi-region deployment
- Relay auto-scaling
- Prometheus + Grafana
- Centralized logging

---

### المرحلة 4: الحجم الكبير (10,000+ مستخدم)

| المكون | المواصفات |
|--------|-----------|
| API | Kubernetes cluster (multi-region) |
| DB | Dedicated PostgreSQL + partitioning |
| Redis | Redis Cluster |
| Relay | Auto-scaling fleet (10+ servers) |
| CDN | Cloudflare Enterprise |
| Monitoring | Full Observability stack |
| Support | Dedicated support team |

---

## 2. استراتيجيات التوسع

### API Scaling

| الاستراتيجية | التفاصيل |
|-------------|----------|
| Horizontal Scaling | إضافة instances خلف Load Balancer |
| Stateless Design | لا يخزّن حالة — كل شيء في DB/Redis |
| Connection Pooling | PgBouncer للـ DB connections |
| Caching | Redis cache للبيانات المتكررة (regions, plans) |
| Rate Limiting | Redis-based token bucket |

### Database Scaling

| الاستراتيجية | متى |
|-------------|-----|
| Connection Pooling | من البداية |
| Indexes | من البداية |
| Read Replicas | 1,000+ مستخدم |
| Table Partitioning | usage_logs (monthly) من البداية |
| Archiving | نقل البيانات القديمة (> 90 يوم) |

### Relay Scaling

| الاستراتيجية | التفاصيل |
|-------------|----------|
| Load Balancing | توزيع العملاء على أقل Relay حملاً |
| Auto-Scaling | إضافة relay عند وصول الحمل لـ 80% |
| Health Checks | كل relay يرسل heartbeat كل 30 ثانية |
| Failover | إذا relay سقط → إعادة تعيين العملاء لـ relay آخر |
| Regional | إضافة مناطق جديدة حسب الطلب |

---

## 3. Performance Targets

| المقياس | الهدف |
|---------|-------|
| API Response Time (p50) | < 50ms |
| API Response Time (p99) | < 500ms |
| Relay Tunnel Setup | < 200ms |
| Proxy Assignment | < 100ms |
| Database Query | < 20ms (p50) |
| Uptime | 99.5% (المرحلة 1-2) → 99.9% (المرحلة 3+) |
| Concurrent Connections per Relay | 500-1000 |

---

## 4. خطة الطوارئ (Disaster Recovery)

| السيناريو | الإجراء |
|-----------|---------|
| API down | Auto-restart + alert → manual investigation |
| DB down | Supabase handles failover → point-in-time recovery |
| Relay down | Auto-failover → clients reconnect to another relay |
| Redis down | API falls back to DB-based rate limiting |
| DDoS | Cloudflare protection + rate limiting |
| Data breach | Revoke all tokens → force password reset → audit |
| Stripe down | Queue payment events → retry when available |

### Backups

| البيانات | التكرار | الاحتفاظ |
|----------|---------|----------|
| PostgreSQL | يومي (Supabase auto) | 7 أيام |
| Redis | لا يحتاج (cache فقط) | - |
| Proxy lists | عند كل import | آخر 5 نسخ |
| Config/Secrets | مشفرة في GitHub Secrets | دائم |

---

## 5. Security Hardening

| الإجراء | التفاصيل |
|---------|----------|
| HTTPS everywhere | TLS 1.3 فقط |
| API key rotation | كل 90 يوم |
| JWT key rotation | كل 6 أشهر |
| Dependency scanning | Dependabot + Snyk |
| Penetration testing | سنوياً (أو عند تغييرات كبيرة) |
| Principle of least privilege | كل service account بأقل صلاحيات |
| Secrets management | ENV vars (never in code) |
| Input validation | على كل endpoint |
| SQL injection | GORM parameterized queries |
| XSS | CSP headers + sanitization |


---
