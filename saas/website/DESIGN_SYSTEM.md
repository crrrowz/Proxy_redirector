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
