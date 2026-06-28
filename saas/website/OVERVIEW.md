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
