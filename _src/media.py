# -*- coding: utf-8 -*-
"""
Görsel türev üreticisi. Yalnızca images/ altına yeni görsel eklendiğinde çalıştır:
    python3 _src/media.py

Kaynak: images/*.webp (kullanıcının yüklediği, 178-484 KB, 1024-1717 px)
Çıktı : images/w500|w900|w1600/<ad>.webp

⚠️ cwebp'nin VARSAYILAN ayarı kullanılmıyor (-m 6 -pass 10): görsel başına ~12,5 sn CPU
   yiyor ve dosyayı %18 BÜYÜTEBİLİYOR (bkz reference_medialibrary_cwebp_optimizer).
   Pillow ile method=4 / quality=82 dengesi kullanılıyor.
⚠️ Kaynaklar SİLİNMİYOR; sayfalara hep türev giriyor.
"""
import os, glob
from PIL import Image

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(KOK, "images")
BOYLAR = (500, 900, 1600)

def uret(zorla=False):
    kaynaklar = sorted(glob.glob(os.path.join(IMG, "*.webp")))
    if not kaynaklar:
        print("images/ altında kaynak görsel yok"); return
    toplam_kaynak = toplam_turev = 0
    for k in kaynaklar:
        taban = os.path.splitext(os.path.basename(k))[0]
        toplam_kaynak += os.path.getsize(k)
        with Image.open(k) as im:
            im = im.convert("RGB")
            gen, yuk = im.size
            # ⚠️ Kaynak en küçük boydan da küçükse (ör. 380px) hiç türev üretilmiyordu
            #    ve gorsel() boş srcset döndürüp görseli SESSİZCE düşürüyordu.
            #    Böyle görseller kendi boyutlarında w500'e yazılıyor.
            boylar = [b for b in BOYLAR if b <= gen] or [gen]
            for b in boylar:
                if b > gen:
                    continue
                # kaynaktan küçük tek boy varsa onu w500 rafına koy (srcset boş kalmasın)
                raf = b if b in BOYLAR else min(BOYLAR)
                klasor = os.path.join(IMG, f"w{raf}")
                os.makedirs(klasor, exist_ok=True)
                hedef = os.path.join(klasor, taban + ".webp")
                if os.path.exists(hedef) and not zorla:
                    toplam_turev += os.path.getsize(hedef); continue
                yeni_yuk = round(yuk * b / gen)
                im.resize((b, yeni_yuk), Image.LANCZOS).save(
                    hedef, "WEBP", quality=82, method=4)
                toplam_turev += os.path.getsize(hedef)
        # en büyük boy kaynaktan küçükse, en yakın boyu da üret ki srcset boş kalmasın
        if gen < min(BOYLAR):
            klasor = os.path.join(IMG, f"w{min(BOYLAR)}")
            os.makedirs(klasor, exist_ok=True)

    print(f"{len(kaynaklar)} kaynak ({toplam_kaynak/1024/1024:.1f} MB) → "
          f"türevler {toplam_turev/1024/1024:.1f} MB")
    for b in BOYLAR:
        n = len(glob.glob(os.path.join(IMG, f"w{b}", "*.webp")))
        if n:
            boyut = sum(os.path.getsize(x) for x in glob.glob(os.path.join(IMG, f"w{b}", "*.webp")))
            print(f"  w{b:<5d} {n:3d} dosya  ort. {boyut/n/1024:5.0f} KB")

def referanslar():
    """Panelden gelen referans görselleri: img/referans/<12hex>.webp → images/referans/<yayın adı>[-N]-{480,900,1600}.webp.
    Referans başına 1–5 görsel; ilki (kapak) eski adını korur, sonrakiler -2…-5 eki alır (build.referans_gorsel_adlari).
    Yayın adı firma adından + id (build.referans_dosya_adi). Artık kullanılmayan türevler silinir.
    ⚠️ Gizli referansın türevi üretilmez — depo herkese açık Pages adresi."""
    import json, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build import referans_gorsel_adlari
    ref = json.load(open(os.path.join(KOK, "_src", "referanslar.json"), encoding="utf-8"))
    dizin = os.path.join(IMG, "referans")
    os.makedirs(dizin, exist_ok=True)
    gecerli = set()
    # yayın adı → kaynak eşlemesi: kapak değişince adlar kayar; eşleme değişen türev, tarih ne olursa olsun yeniden üretilir
    harita_yol = os.path.join(KOK, "_src", "referans_harita.json")
    try:
        eski = json.load(open(harita_yol, encoding="utf-8"))
    except (OSError, ValueError):
        eski = {}
    harita = {}
    for r in ref:
        if not r.get("gorunur"):
            continue
        for g, ad in zip(r.get("gorseller") or [r["id"]], referans_gorsel_adlari(r)):
            kaynak = os.path.join(KOK, "img", "referans", g + ".webp")
            if not os.path.exists(kaynak):
                continue
            harita[ad] = g
            im = None
            for w in (480, 900, 1600):
                hedef = os.path.join(dizin, f"{ad}-{w}.webp")
                gecerli.add(os.path.basename(hedef))
                if (eski.get(ad) == g and os.path.exists(hedef)
                        and os.path.getmtime(hedef) >= os.path.getmtime(kaynak)):
                    continue
                im = im or Image.open(kaynak).convert("RGB")
                t = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
                t.save(hedef, "WEBP", quality=80, method=4)
    with open(harita_yol, "w", encoding="utf-8") as f:
        json.dump(harita, f, ensure_ascii=False, indent=1, sort_keys=True)
    for f in os.listdir(dizin):
        if f not in gecerli:
            os.remove(os.path.join(dizin, f))
    print(f"{len(gecerli) // 3} referans görseli hazır")  # görsel sayısı (referans başına 1–5)

if __name__ == "__main__":
    import sys
    if "--referans" in sys.argv:   # panel yayını: yalnız referanslar (referans_yayinla.sh)
        referanslar()
    else:
        uret(zorla="--zorla" in sys.argv)
        referanslar()
