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
            for b in BOYLAR:
                # Kaynaktan büyük türev üretme — büyütmek dosyayı şişirir, kalite katmaz.
                if b > gen:
                    continue
                klasor = os.path.join(IMG, f"w{b}")
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

if __name__ == "__main__":
    import sys
    uret(zorla="--zorla" in sys.argv)
