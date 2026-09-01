# -*- coding: utf-8 -*-
"""
Üretilen siteyi denetler. ⚠️ COMMIT ÖNCESİ çalıştır — hata varsa 1 döner.

Kontroller: kırık iç link/görsel · tekrar eden veya uzun title/description ·
canonical · çoklu H1 · beyaz liste dışı dış kaynak · teyit edilmemiş iddia.
"""
import os, re, sys, collections, html as H

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ⚠️ Bu hostlar dışındaki HER dış istek hata sayılır. Google Maps facade
#    arkasında (tıklanmadan istek gitmiyor); www.web4medya.com yalnız bağlantı.
DIS_BEYAZ = {"dehaiskele.com", "www.dehaiskele.com",   # kendi alan adı (canonical/og:url)
            "wa.me", "www.google.com", "maps.google.com", "www.web4medya.com"}

# ⏳ Kullanıcı onaylamadan sayfaya girmemesi gereken iddialar.
# 7/24 · sigortalı · ücretsiz keşif → kullanıcı 2026-09-01'de TEYİT ETTİ, listeden çıktı.
YASAK_IDDIA = [
    "sertifikalı", "TSE belgeli", "CE belgeli",   # 10+ yıl deneyim PDF ile teyitli, çıkarıldı
    "depozitosuz", "indirimli paket", "kampanya",
]
# ⛔ Üstünlük iddiası — Ticari Reklam Yönetmeliği gereği ispat istiyor, yazılmaz.
YASAK_USTUNLUK = ["en iyi", "en kaliteli", "bir numara", "lider firma", "türkiye'nin en"]

sayfalar, hata, uyari = [], [], []
for kok, _, dosyalar in os.walk(KOK):
    if "/.git" in kok or "/_src" in kok:
        continue
    for d in dosyalar:
        if d.endswith(".html"):
            sayfalar.append(os.path.join(kok, d))

def var_mi(yol):
    yol = yol.split("#")[0].split("?")[0]
    if not yol.startswith("/"):
        return True
    t = os.path.join(KOK, yol.strip("/"))
    return (os.path.exists(t) or os.path.exists(os.path.join(t, "index.html"))
            or os.path.exists(t + ".html"))

basliklar, aciklamalar = collections.Counter(), collections.Counter()
for s in sorted(sayfalar):
    ic = open(s, encoding="utf-8").read()
    rel = "/" + os.path.relpath(s, KOK)

    for u in set(re.findall(r'href="(/[^"]*)"', ic)) | set(re.findall(r'src="(/[^"]*)"', ic)):
        if not var_mi(u):
            hata.append(f"KIRIK  {rel} → {u}")
    for u in set(re.findall(r'srcset="([^"]+)"', ic)):
        for p in [x.strip().split(" ")[0] for x in u.split(",")]:
            if p.startswith("/") and not var_mi(p):
                hata.append(f"KIRIK GÖRSEL  {rel} → {p}")

    for host in set(re.findall(r'(?:href|src)="https?://([^/"]+)', ic)):
        if host not in DIS_BEYAZ:
            hata.append(f"DIŞ KAYNAK  {rel} → {host}")

    # ⚠️ Uzunluk html.unescape SONRASI ölçülür: "Şile&#x27;de" ham hâlde 6 fazla sayılıyor.
    t = re.search(r"<title>(.*?)</title>", ic, re.S)
    a = re.search(r'<meta name="description" content="(.*?)"', ic, re.S)
    t = H.unescape(t.group(1)) if t else None
    a = H.unescape(a.group(1)) if a else None
    if t:
        basliklar[t] += 1
        if len(t) > 70: hata.append(f"UZUN TITLE ({len(t)})  {rel}")
    if a:
        aciklamalar[a] += 1
        if not (110 <= len(a) <= 175): hata.append(f"DESC UZUNLUK ({len(a)})  {rel}")
    if 'rel="canonical"' not in ic: hata.append(f"CANONICAL YOK  {rel}")
    if ic.count("<h1") != 1: hata.append(f"H1 SAYISI {ic.count('<h1')}  {rel}")

    govde = re.sub(r"<script.*?</script>", "", ic, flags=re.S).lower()
    for kelime in YASAK_IDDIA:
        if kelime in govde:
            uyari.append(f"TEYİTSİZ İDDİA '{kelime}'  {rel}")
    for kelime in YASAK_USTUNLUK:
        if kelime in govde:
            hata.append(f"ÜSTÜNLÜK İDDİASI '{kelime}'  {rel}")

for b, n in basliklar.items():
    if n > 1: hata.append(f"TEKRAR TITLE ×{n}: {b[:70]}")
for b, n in aciklamalar.items():
    if n > 1: hata.append(f"TEKRAR DESC ×{n}: {b[:70]}")

print(f"{len(sayfalar)} sayfa denetlendi")
if uyari:
    o = collections.Counter(u.split("  ")[0] for u in uyari)
    print("\n⏳ TEYİT BEKLEYEN İDDİALAR:")
    for k, v in o.most_common(): print(f"  {v:4d} × {k}")
if hata:
    ozet = collections.Counter(h.split("  ")[0].split(" (")[0] for h in hata)
    print("\n❌ HATALAR:")
    for k, v in ozet.most_common(): print(f"  {v:4d} × {k}")
    print()
    for h in hata[:25]: print("   ", h)
    if len(hata) > 25: print(f"    … {len(hata)-25} tane daha")
    sys.exit(1)
print("✓ hata yok")
