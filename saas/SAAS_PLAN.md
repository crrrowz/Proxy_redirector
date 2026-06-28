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
