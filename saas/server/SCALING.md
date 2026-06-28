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
