import os

SAAS_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(SAAS_DIR, "FULL_PLAN.md")

FOLDER_TITLES = {
    "website": "🌐 الموقع التسويقي (Website)",
    "client-app": "🖥️ تطبيق العميل (Client App)",
    "server": "☁️ السيرفر والبنية التحتية (Server)",
}

FOLDER_ORDER = ["website", "client-app", "server"]

parts = []
parts.append("# 📦 Proxy Redirector SaaS — الخطة الكاملة\n")
parts.append("> تم الدمج تلقائياً — جميع ملفات `saas/` في ملف واحد\n")
parts.append("---\n\n")

# README first
readme = os.path.join(SAAS_DIR, "README.md")
if os.path.isfile(readme):
    with open(readme, "r", encoding="utf-8") as f:
        parts.append(f.read().strip())
    parts.append("\n\n---\n\n")

SAAS_PLAN = os.path.join(SAAS_DIR, "SAAS_PLAN.md")
if os.path.isfile(SAAS_PLAN):
    with open(SAAS_PLAN, "r", encoding="utf-8") as f:
        parts.append(f.read().strip())
    parts.append("\n\n---\n\n")

for folder in FOLDER_ORDER:
    folder_path = os.path.join(SAAS_DIR, folder)
    if not os.path.isdir(folder_path):
        continue

    title = FOLDER_TITLES.get(folder, folder)
    parts.append(f"\n\n{'=' * 80}\n")
    parts.append(f"# {title}\n")
    parts.append(f"{'=' * 80}\n\n")

    files = sorted(f for f in os.listdir(folder_path) if f.endswith(".md"))
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        parts.append(f"\n<!-- ═══ {folder}/{filename} ═══ -->\n\n")
        parts.append(content)
        parts.append("\n\n---\n")

merged = "\n".join(parts)

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(merged)

size_kb = os.path.getsize(OUTPUT) / 1024
print(f"✅ تم الدمج → {OUTPUT}")
print(f"   الحجم: {size_kb:.1f} KB")
