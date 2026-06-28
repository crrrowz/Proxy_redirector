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
