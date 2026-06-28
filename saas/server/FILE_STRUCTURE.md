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
