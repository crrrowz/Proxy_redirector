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
