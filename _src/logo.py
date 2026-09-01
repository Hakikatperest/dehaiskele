# -*- coding: utf-8 -*-
"""
Geçici marka işareti ve favicon üreticisi.

⏳ GEÇİCİ: gerçek Deha İskele logosu gelince bu dosya onun türevlerini üretecek
   şekilde değiştirilecek (emsal: seyrannakliyat/_src/logo.py).

⚠️ Google favicon kuralları (bkz reference_google_favicon_kurallari):
   - WebP KABUL EDİLMEZ → ico/png üretiliyor
   - kare ve 48'in katı → 48/96/192
   - apple-touch-icon beyaz zeminli (iOS saydamı SİYAHA çeviriyor)
   - Organization/logo alanı için min 112×112 → logo-512.png

Çalıştırma: python3 _src/logo.py   (görsel değişmedikçe tekrar çalıştırmaya gerek yok)
"""
import os
from PIL import Image, ImageDraw

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(KOK, "images")
os.makedirs(IMG, exist_ok=True)

KOYU = (18, 22, 28, 255)
SARI = (255, 194, 51, 255)
BEYAZ = (255, 255, 255, 255)

def isaret(boy, zemin=KOYU, cizgi=SARI):
    """İskele çerçevesi (H tipi) siluetinden türetilmiş işaret."""
    o = 4                                   # süper örnekleme
    b = boy * o
    im = Image.new("RGBA", (b, b), zemin)
    d = ImageDraw.Draw(im)
    p = int(b * 0.155)                      # kenar payı
    k = max(2, int(b * 0.052))              # çizgi kalınlığı
    x0, y0, x1, y1 = p, p, b - p, b - p

    d.rectangle([x0, y0, x1, y1], outline=cizgi, width=k)          # dış çerçeve
    for oran in (0.333, 0.667):                                     # yatay kuşaklar
        y = y0 + (y1 - y0) * oran
        d.line([x0, y, x1, y], fill=cizgi, width=k)
    for oran in (0.333, 0.667):                                     # dikey dikmeler
        x = x0 + (x1 - x0) * oran
        d.line([x, y0, x, y1], fill=cizgi, width=k)
    ky = int(k * 0.85)                                              # çaprazlar
    d.line([x0, y0 + (y1 - y0) * 0.333, x0 + (x1 - x0) * 0.333, y1], fill=cizgi, width=ky)
    d.line([x0 + (x1 - x0) * 0.667, y0 + (y1 - y0) * 0.333, x1, y1], fill=cizgi, width=ky)
    return im.resize((boy, boy), Image.LANCZOS)

def yaz():
    uretilen = []
    for boy in (48, 96, 192):
        y = os.path.join(IMG, f"favicon-{boy}.png")
        isaret(boy).save(y, "PNG", optimize=True)
        uretilen.append(y)

    # /favicon.ico — çok boyutlu (16/32/48)
    ico = os.path.join(KOK, "favicon.ico")
    isaret(192).save(ico, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    uretilen.append(ico)

    # apple-touch-icon: iOS saydamı siyaha çeviriyor → zemin açık bırakılmıyor,
    # koyu marka zemini zaten opak.
    at = os.path.join(IMG, "apple-touch-icon.png")
    isaret(180).save(at, "PNG", optimize=True)
    uretilen.append(at)

    # Organization/logo alanı (min 112×112)
    lg = os.path.join(IMG, "logo-512.png")
    isaret(512).save(lg, "PNG", optimize=True)
    uretilen.append(lg)

    for y in uretilen:
        print(f"  {os.path.relpath(y, KOK):34s} {os.path.getsize(y):>7,} B")
    print(f"{len(uretilen)} dosya üretildi")

if __name__ == "__main__":
    yaz()
