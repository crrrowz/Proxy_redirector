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
