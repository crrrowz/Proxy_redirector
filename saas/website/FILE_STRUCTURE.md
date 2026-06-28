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
