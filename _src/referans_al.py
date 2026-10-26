# -*- coding: utf-8 -*-
"""Panelden (panel.dehaiskele.com) gelen referans verisini depoya alır.
Kullanım: python3 _src/referans_al.py /home/panel.dehaiskele.com/veri
- veri/referanslar.json → _src/referanslar.json (alanlar süzülür, tipler zorlanır)
- veri/gorseller/<12hex>.webp → img/referans/<12hex>.webp — YALNIZ görünürler; gizli/silinenler silinir
- Referans başına 1–5 görsel (`gorseller`, ilki kapak; eski kayıtta yalnız `gorsel`) → _src'de `gorseller` = 12hex listesi
- data.TURLER / data.ILCELER → veri/secenekler.json (paneldeki "iskele türü" ve "ilçe" listeleri senkron kalsın)
⚠️ Panel verisi GÜVENİLMEZ girdi sayılır: id/görsel adı regex'le doğrulanır, metin build'de kaçışlanır."""
import json, os, re, shutil, sys
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D

veri = sys.argv[1]
ham = json.load(open(os.path.join(veri, "referanslar.json"), encoding="utf-8"))
turler = {t["slug"] for t in D.TURLER}
ilceler = {i["slug"] for i in D.ILCELER}
temiz, kullanilan = [], set()
for r in ham:
    rid = str(r.get("id", ""))
    liste = r.get("gorseller") or ([r["gorsel"]] if r.get("gorsel") else [])
    gorseller = [str(g)[:-5] for g in liste if re.fullmatch(r"[a-f0-9]{12}\.webp", str(g))
                 and os.path.isfile(os.path.join(veri, "gorseller", str(g)))][:5]
    if not re.fullmatch(r"[a-f0-9]{12}", rid) or not gorseller:
        continue
    temiz.append({
        "id": rid,
        "firma": str(r.get("firma", ""))[:80].strip(),
        "aciklama": str(r.get("aciklama", ""))[:700].strip(),
        "tur": r.get("tur") if r.get("tur") in turler else "",
        "ilce": r.get("ilce") if r.get("ilce") in ilceler else "",
        "gorunur": bool(r.get("gorunur")),
        "sira": int(r.get("sira", 0)),
        "tarih": str(r.get("tarih", ""))[:25],
        "gorseller": gorseller,
    })
    # ⚠️ Gizli referansın görseli depoya (= herkese açık Pages adresine) KOPYALANMAZ.
    if r.get("gorunur"):
        kullanilan.update(g + ".webp" for g in gorseller)
temiz.sort(key=lambda r: (r["sira"], r["tarih"]))
hedef = os.path.join(KOK, "img", "referans")
os.makedirs(hedef, exist_ok=True)
for g in kullanilan:
    shutil.copyfile(os.path.join(veri, "gorseller", g), os.path.join(hedef, g))
for f in os.listdir(hedef):
    if f not in kullanilan:
        os.remove(os.path.join(hedef, f))
with open(os.path.join(KOK, "_src", "referanslar.json"), "w", encoding="utf-8") as f:
    json.dump(temiz, f, ensure_ascii=False, indent=1)
with open(os.path.join(veri, "secenekler.json"), "w", encoding="utf-8") as f:
    json.dump({"tur": {t["slug"]: t["ad"] for t in D.TURLER},
               "ilce": {i["slug"]: i["ad"] for i in D.ILCELER}},
              f, ensure_ascii=False, indent=1)
print(f"{len(temiz)} referans alındı ({sum(r['gorunur'] for r in temiz)} görünür)")
