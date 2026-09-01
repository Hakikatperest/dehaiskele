# -*- coding: utf-8 -*-
"""
Marka logosu türevleri ve favicon üreticisi.
Kaynak: images/deha-iskele-logo.png (1536×1024, kullanıcı 2026-09-01'de verdi)

Çalıştırma: python3 _src/logo.py    (logo değişmedikçe tekrar çalıştırma gerekmez)

⚠️ Kaynak PNG 237 KB — sitede DOĞRUDAN KULLANILMAZ, hep türev basılır.
⚠️ İki varyant şart: özgün logodaki "DEHA" yazısı metalik GRİ; koyu alt bilgi zemininde
   sönük kalıyor. `-ak` varyantında gri pikseller beyaza çekiliyor (turuncu korunuyor).
⚠️ Google favicon kuralları: WebP KABUL EDİLMEZ, kare ve 48'in katı olmalı
   (bkz reference_google_favicon_kurallari). Favicon logonun sol bloğundan
   (iskele kulesi + "D") kare kırpılıyor — tam logo 48px'te okunmuyor.
"""
import os
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(KOK, "images")
KAYNAK = os.path.join(IMG, "deha-iskele-logo.png")
KOYU = (21, 24, 29, 255)

def yukle():
    im = Image.open(KAYNAK).convert("RGBA")
    # Beyaz zemini şeffaflaştır
    px = im.load()
    g, y = im.size
    for j in range(y):
        for i in range(g):
            r, gg, b, a = px[i, j]
            if r > 240 and gg > 240 and b > 240:
                px[i, j] = (r, gg, b, 0)
    return im.crop(im.getbbox())          # çevredeki boşluğu at

def acik_varyant(im):
    """Koyu zemin için: gri/siyah pikselleri beyaza çek, turuncuyu koru."""
    im = im.copy()
    px = im.load()
    g, y = im.size
    for j in range(y):
        for i in range(g):
            r, gg, b, a = px[i, j]
            if a == 0:
                continue
            turuncu_mu = r > 150 and gg < 170 and b < 110 and (r - b) > 90
            if not turuncu_mu:
                t = max(r, gg, b)
                yeni = 255 if t > 40 else 210        # koyu gölgeler de görünür kalsın
                px[i, j] = (yeni, yeni, yeni, a)
    return im

def kaydet(im, ad, boy):
    """⚠️ Logo WebP olarak basılıyor — PNG'nin 4'te biri boyutta. Favicon WebP OLAMAZ
    (Google kabul etmiyor), o yüzden yalnız logo türevleri WebP."""
    o = im.copy()
    o.thumbnail((boy, boy * 4), Image.LANCZOS)
    y = os.path.join(IMG, "logo", f"{ad}-{boy}.webp")
    os.makedirs(os.path.dirname(y), exist_ok=True)
    o.save(y, "WEBP", quality=88, method=4, lossless=False)
    return y, o.size

def isaret(im, boy, zemin=None):
    """Favicon işareti: logonun sol bloğu (iskele kulesi + D) kare kırpılır."""
    g, y = im.size
    kare = im.crop((0, 0, int(g * 0.40), y))
    kg, ky = kare.size
    k = min(kg, ky)
    kare = kare.crop(((kg - k) // 2, (ky - k) // 2, (kg - k) // 2 + k, (ky - k) // 2 + k))
    kare = kare.resize((boy, boy), Image.LANCZOS)
    if zemin:
        alt = Image.new("RGBA", (boy, boy), zemin)
        alt.alpha_composite(kare)
        return alt.convert("RGB") if zemin[3] == 255 else alt
    return kare

def main():
    im = yukle()
    print(f"kaynak kırpıldı: {im.size[0]}×{im.size[1]}")
    ak = acik_varyant(im)
    uretilen = []
    for boy in (200, 320, 480, 680):
        uretilen.append(kaydet(im, "deha-logo", boy))
        uretilen.append(kaydet(ak, "deha-logo-ak", boy))

    # Favicon: koyu marka zeminli kare (şeffaf favicon küçük boyutta kayboluyor)
    # ⚠️ Favicon'lar palete indiriliyor: düz renkli marka işaretinde 256 renk
    #    yeterli ve dosya 4-5 kat küçülüyor.
    for boy in (48, 96, 192):
        y = os.path.join(IMG, f"favicon-{boy}.png")
        isaret(im, boy, KOYU).quantize(colors=128, method=Image.MEDIANCUT).save(
            y, "PNG", optimize=True)
        uretilen.append((y, (boy, boy)))
    isaret(im, 192, KOYU).save(os.path.join(KOK, "favicon.ico"), "ICO",
                               sizes=[(16, 16), (32, 32), (48, 48)])
    # apple-touch-icon: iOS saydamı SİYAHA çeviriyor → opak zemin şart
    isaret(im, 180, KOYU).quantize(colors=128).save(
        os.path.join(IMG, "apple-touch-icon.png"), "PNG", optimize=True)
    # Organization/logo alanı (min 112×112)
    isaret(im, 512, KOYU).quantize(colors=200).save(
        os.path.join(IMG, "logo-512.png"), "PNG", optimize=True)

    for y, boyut in uretilen:
        print(f"  {os.path.relpath(y, KOK):34s} {boyut[0]:4d}×{boyut[1]:<4d} "
              f"{os.path.getsize(y)/1024:6.1f} KB")

if __name__ == "__main__":
    main()
