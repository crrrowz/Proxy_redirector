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
