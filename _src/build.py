# -*- coding: utf-8 -*-
"""
dehaiskele.com üreticisi.

⛔ Üretilen HTML'i ELLE DÜZENLEME — bu betik her çalıştığında üzerine yazar.
   Metin ve veri değişikliği `data.py`'ye yapılır.

Çalıştırma:  python3 _src/build.py     (kök dizine 53 sayfa + sitemap/robots/404 yazar)
Denetim:     python3 _src/denetim.py   (commit ÖNCESİ çalıştır, hatada 1 döner)
"""
import os, re, sys, html, hashlib, collections, json

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D

S = D.SITE
ALAN = S["alan"]

# ── Varlık sürümleme ────────────────────────────────────────────────────────
# GitHub Pages CSS/JS'i max-age=600 ile servis ediyor. Adres sabit kalırsa
# tarayıcı yeni HTML'i eski CSS'le birleştiriyor (duvarkagidikaplama'da yaşandı:
# stilsiz kalan SVG 300×150 varsayılan boyutuyla dev göründü). ⛔ Kaldırma.
_surum_onbellek = {}
def surum(yol):
    if yol not in _surum_onbellek:
        t = os.path.join(KOK, yol.lstrip("/"))
        try:
            h = hashlib.md5(open(t, "rb").read()).hexdigest()[:8]
        except FileNotFoundError:
            h = "0"
        _surum_onbellek[yol] = f"{yol}?v={h}"
    return _surum_onbellek[yol]

def e(t):
    return html.escape(str(t), quote=True)

def kirp(metin, en_az=115, en_cok=168):
    """meta description'ı denetimin kabul ettiği aralığa çeker."""
    m = " ".join(metin.split())
    if len(m) > en_cok:
        kes = m[:en_cok]
        if " " in kes:
            kes = kes[:kes.rfind(" ")]
        m = kes.rstrip(" ,;:.") + "."
    return m

# ── Komşuluk grafiği ────────────────────────────────────────────────────────
# data.py'de bağlar tek yönlü yazılmış olabilir; iki yönlü hale getiriliyor
# (seyrannakliyat'ta 7 bağ tek yönlüydü, ilçeler birbirine link vermiyordu).
ILCE = {i["slug"]: i for i in D.ILCELER}
def komsuluk_kur():
    g = collections.defaultdict(set)
    for i in D.ILCELER:
        for k in i["komsu"]:
            if k in ILCE:
                g[i["slug"]].add(k)
                g[k].add(i["slug"])
    return {k: sorted(v) for k, v in g.items()}
KOMSU = komsuluk_kur()


# ── Türkçe ek ────────────────────────────────────────────────────────────────
# ⛔ Kod içinde "{ad}'da" gibi elle ek YAZMA. Ünlü uyumu + kaynaştırma harfi
#    ilçeye göre değişiyor (Beşiktaş'ta, Beylikdüzü'nde, Ümraniye'de).

def kucuk(s):
    """⚠️ Türkçe küçük harf. Python'un .lower()'ı 'İ' harfini 'i̇' (i + birleşen nokta)
    yapıyor; anchor metinlerinde 'i̇skele' diye bozuk çıkıyordu."""
    return s.replace("İ", "i").replace("I", "ı").lower()

def ek(i, hal="loc"):
    """i: ilçe dict'i (veya slug). hal: loc(-de) / dat(-e) / gen(-in) / abl(-den)"""
    slug = i if isinstance(i, str) else i["slug"]
    ad = ILCE[slug]["ad"]
    l, d, g, a = D.ILCE_EK[slug]
    return ad + {"loc": l, "dat": d, "gen": g, "abl": a}[hal]

def merkeze_uzaklik(slug):
    """Eyüpsultan'daki merkezden kaç ilçe atlayarak gidiliyor (BFS).
    ⚠️ Kilometre UYDURULMAZ — sadece bu graf mesafesi cümleye dönüşür."""
    baslangic = S["merkez_slug"]
    if slug == baslangic:
        return 0
    gorulen, sira = {baslangic}, [(baslangic, 0)]
    while sira:
        d, u = sira.pop(0)
        for k in KOMSU.get(d, []):
            if k not in gorulen:
                if k == slug:
                    return u + 1
                gorulen.add(k)
                sira.append((k, u + 1))
    return None

def merkez_cumlesi(i):
    u = merkeze_uzaklik(i["slug"])
    m = S["merkez_ilce"] + "'da"        # Eyüpsultan'da
    if u == 0:
        return f"Depomuz {m}, yani {i['ad']} bizim kendi ilçemiz; ekip ve malzeme aynı noktadan çıkıyor."
    if u == 1:
        return f"Depomuz {m}, {ek(i, 'dat')} komşu ilçe; malzeme aynı gün yola çıkıyor."
    if u == 2:
        return f"Depomuz {m}; {ek(i, 'dat')} araç tek güzergâhla ulaşıyor, kurulum günü sabah başlıyor."
    return f"Depomuz {m}; {i['ad']} tarafına giden araç günü baştan planlanarak çıkıyor."

# ── Görsel ──────────────────────────────────────────────────────────────────
# ⚠️ picture varsayılan olarak satır içi; CSS'te picture{display:block} var.
#    srcset dosya sisteminden okunur, sabit liste yazmak 404 üretir.
GENISLIKLER = (500, 900, 1600)
def olcu(taban):
    """Gerçek türevden en/boy okur; sabit oran yazmak yerleşim kayması yapıyordu."""
    for g in GENISLIKLER:
        y = os.path.join(KOK, "images", f"w{g}", taban + ".webp")
        if os.path.exists(y):
            try:
                from PIL import Image
                with Image.open(y) as im:
                    return im.size
            except Exception:
                return (g, int(g * 2 / 3))
    return None

def gorsel_var(taban):
    return any(os.path.exists(os.path.join(KOK, "images", f"w{g}", taban + ".webp"))
               for g in GENISLIKLER)

def gorsel(taban, alt, sinif="", boy="(min-width:1000px) 720px, 100vw", oncelik=False):
    """Görsel yoksa BOŞ döner — placeholder kutusu basmaz, sayfa görselsiz de düzgün akar."""
    if not gorsel_var(taban):
        return ""
    kaynak = []
    for g in GENISLIKLER:
        y = f"/images/w{g}/{taban}.webp"
        if os.path.exists(os.path.join(KOK, y.lstrip("/"))):
            kaynak.append(f"{y} {g}w")
    o = olcu(taban)
    boyut = f' width="{o[0]}" height="{o[1]}"' if o else ""
    yukle = ' loading="eager" fetchpriority="high"' if oncelik else ' loading="lazy" decoding="async"'
    return (f'<picture class="{sinif}"><img src="{kaynak[-1].split(" ")[0]}" '
            f'srcset="{", ".join(kaynak)}" sizes="{boy}" alt="{e(alt)}"{boyut}{yukle}></picture>')

# ── Ortak parçalar ──────────────────────────────────────────────────────────
def tel_btn(sinif="dg dg-sari", metin=None):
    return (f'<a class="{sinif}" href="tel:{S["tel_link"]}" '
            f'data-ara="1">{svg_tel()}<span>{e(metin or S["tel"])}</span></a>')

def tel2_btn(sinif="dg dg-hat2", metin=None):
    """İkinci hat. ⚠️ Birinci numara her yerde birincil kalıyor; bu düğme onun
    yanında ikincil görünümde duruyor ki hangisinin ana hat olduğu belirsizleşmesin."""
    return (f'<a class="{sinif}" href="tel:{S["tel2_link"]}" '
            f'data-ara="2">{svg_tel()}<span>{e(metin or S["tel2"])}</span></a>')

def wa_btn(mesaj="Merhaba, iskele kiralama için bilgi almak istiyorum.", sinif="dg dg-wa"):
    from urllib.parse import quote
    return (f'<a class="{sinif}" href="https://wa.me/{S["wa"]}?text={quote(mesaj)}" '
            f'target="_blank" rel="noopener">{svg_wa()}<span>WhatsApp</span></a>')

# ⚠️ Satır içi SVG'lere HER ZAMAN açık width/height ver: CSS hiç gelmezse
#    varsayılan 300×150 ile devleşiyorlar (duvarkagidikaplama'da yaşandı).
def svg_tel():
    return ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
            '<path d="M6.6 10.8a15.1 15.1 0 006.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.2.4 2.4.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.8 21 3 13.2 3 3.6c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.4 0 .8-.2 1l-2.3 2.6z"/></svg>')

def svg_instagram():
    return ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="1.9">'
            '<rect x="3" y="3" width="18" height="18" rx="5.2"/>'
            '<circle cx="12" cy="12" r="4"/>'
            '<circle cx="17.4" cy="6.6" r="1.1" fill="currentColor" stroke="none"/></svg>')

def svg_saat():
    return ('<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round">'
            '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/></svg>')

def svg_wa():
    return ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
            '<path d="M12 2a10 10 0 00-8.6 15L2 22l5.2-1.4A10 10 0 1012 2zm0 18a8 8 0 01-4.1-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8 8 0 1112 20zm4.4-5.8c-.2-.1-1.4-.7-1.6-.8-.2-.1-.4-.1-.5.1l-.7.9c-.1.2-.3.2-.5.1a6.5 6.5 0 01-3.2-2.8c-.1-.2 0-.4.1-.5l.4-.5c.1-.2.1-.3 0-.5l-.7-1.6c-.2-.4-.4-.4-.5-.4h-.5c-.2 0-.5.1-.7.3a3 3 0 00-.9 2.2c0 1.3.9 2.5 1.1 2.7 1.3 2 2.8 2.9 4.6 3.4 1.1.3 1.7.3 2.2.2.6-.1 1.4-.6 1.6-1.2.2-.6.2-1.1.1-1.2 0-.1-.2-.2-.4-.3z"/></svg>')

def logo(koyu_zemin=False, buyuk=False):
    """Gerçek marka logosu (kullanıcı 2026-09-01'de verdi).
    ⚠️ İKİ VARYANT ŞART: özgün logodaki "DEHA" yazısı metalik gri; koyu alt bilgi
       zemininde sönük kalıyor. koyu_zemin=True → beyaza çekilmiş `-ak` varyantı.
    ⚠️ Kaynak PNG (237 KB) doğrudan kullanılmaz; türevler _src/logo.py üretir."""
    ad = "deha-logo-ak" if koyu_zemin else "deha-logo"
    kaynak = ", ".join(f"/images/logo/{ad}-{b}.webp {b}w" for b in (200, 320, 480, 680))
    # ⚠️ Alt bilgi logosu 301px genişlikte basılıyor; üst bar için yazılan sizes
    #    (92px) yüzünden tarayıcı 200w türevini seçip logoyu geriyordu (bulanık).
    olcu = "(min-width:860px) 310px, 180px" if buyuk else "(min-width:860px) 115px, 90px"
    return (f'<span class="logo">'
            f'<img src="/images/logo/{ad}-320.webp" srcset="{kaynak}" '
            f'sizes="{olcu}" width="320" height="220" '
            f'alt="{e(S["marka"])} — İstanbul iskele kiralama" '
            f'class="logo-im" decoding="async"></span>')

MENU = [
    ("/", "Ana Sayfa"),
    ("/hakkimizda/", "Hakkımızda"),
    ("/iskele-cesitleri/", "İskele Çeşitleri"),
    ("/iskele-kiralama-fiyatlari/", "Fiyatlar"),
    ("/iskele-is-guvenligi/", "İş Güvenliği"),
    ("/ilceler/", "İlçeler"),
]

def head(baslik, aciklama, yol, schema=""):
    kanonik = ALAN + yol
    ac = kirp(aciklama)
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script async src="{D.TAKIP_SRC}" data-key="{D.TAKIP_KEY}"></script>
<title>{e(baslik)}</title>
<meta name="description" content="{e(ac)}">
<link rel="canonical" href="{e(kanonik)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(S['marka'])}">
<meta property="og:title" content="{e(baslik)}">
<meta property="og:description" content="{e(ac)}">
<meta property="og:url" content="{e(kanonik)}">
<meta property="og:locale" content="tr_TR">
<meta name="theme-color" content="#12161c">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/images/favicon-48.png" sizes="48x48">
<link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
<link rel="stylesheet" href="{surum('/assets/style.css')}">
<script>document.documentElement.classList.add('js')</script>
{schema}
</head>
<body>
<a class="atla" href="#ana">İçeriğe geç</a>
"""

def teklif_btn(sinif="dg dg-teklif"):
    """Referans kurumsal düzendeki "TEKLİF AL" düğmesi. Statik site olduğu için
    form yok — WhatsApp'a hazır mesajla gidiyor."""
    from urllib.parse import quote
    m = quote("Merhaba, iskele kiralama için teklif almak istiyorum.")
    return (f'<a class="{sinif}" href="https://wa.me/{S["wa"]}?text={m}" '
            f'target="_blank" rel="noopener"><span>Teklif Al</span>'
            f'<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" fill="none" '
            f'stroke="currentColor" stroke-width="2.4" stroke-linecap="round">'
            f'<path d="M7 17L17 7M8 7h9v9"/></svg></a>')

def ust_serit():
    """İnce iletişim şeridi — iki telefon, WhatsApp, adres."""
    return f"""<div class="ust-serit">
  <div class="kap ust-serit-ic">
    <div class="us-sol">
      <a href="tel:{S['tel_link']}">{svg_tel()}<span>{e(S['tel'])}</span></a>
      <a href="tel:{S['tel2_link']}">{svg_tel()}<span>{e(S['tel2'])}</span></a>
      <a href="https://wa.me/{S['wa']}" target="_blank" rel="noopener">{svg_wa()}<span>WhatsApp</span></a>
    </div>
    <div class="us-sag">
      <span class="us-saat">{svg_saat()}<span>{e(S['saat'])}</span></span>
      <span class="us-rozet">10+ yıl deneyim</span>
    </div>
  </div>
</div>"""

def ust_header(aktif=""):
    parcalar = []
    for u, m in MENU:
        sinif = ' class="aktif"' if u == aktif else ""
        parcalar.append('<a href="%s"%s>%s</a>' % (u, sinif, e(m)))
    ln = "".join(parcalar)
    return f"""<div class="ust-kap">
{ust_serit()}
<header class="ust">
  <div class="kap ust-ic">
    <a class="logo-bag" href="/" aria-label="{e(S['marka'])} ana sayfa">{logo()}</a>
    <nav class="menu" id="menu" aria-label="Ana menü">{ln}</nav>
    <div class="ust-ara">
      <a class="ust-tel" href="tel:{S['tel_link']}">
        <span class="ust-tel-ik">{svg_tel()}</span>
        <span class="ust-tel-ic"><small>Hemen arayın</small><strong>{e(S['tel'])}</strong></span>
      </a>
      {teklif_btn("dg dg-teklif")}
      <button class="hamburger" id="hamburger" aria-label="Menüyü aç" aria-expanded="false" aria-controls="menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>
</div>
"""

def kirinti(parcalar):
    """parcalar: [(ad, url|None)] — son eleman linksiz."""
    ic, ldj = [], []
    for n, (ad, u) in enumerate(parcalar, 1):
        ic.append(f'<a href="{u}">{e(ad)}</a>' if u else f'<span aria-current="page">{e(ad)}</span>')
        ldj.append({"@type": "ListItem", "position": n, "name": ad,
                    **({"item": ALAN + u} if u else {})})
    sema = ('<script type="application/ld+json">' +
            json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                        "itemListElement": ldj}, ensure_ascii=False) + '</script>')
    return f'<nav class="kirinti" aria-label="Site haritası"><div class="kap">{"".join(ic)}</div></nav>{sema}'

def w4_kredi():
    """Web4Medya tasarım imzası.
    ⚠️ Bağlantı YALNIZCA marka adını sarar — 'Web Tasarım:' etiketi <a> DIŞINDA kalır.
    53 sayfadan çıkan site geneli anahtar kelimeli tasarımcı linki Google'ın link
    şeması tarifine girer. Kullanıcı risk tablosunu görüp bunu seçti. ⛔ Geri çevirme."""
    return ('<div class="w4"><span class="w4-bag">'
            '<span class="w4-etiket">Web Tasarım:</span> '
            '<a class="w4-ad" href="https://www.web4medya.com/" target="_blank" rel="noopener">'
            'Web<span class="w4-d">4</span>Medya</a></span></div>')

def sosyal_baglantilar():
    ikon = {"instagram": svg_instagram}
    return "".join(
        f'<a class="sos sos-{k}" href="{e(u)}" target="_blank" rel="noopener" '
        f'aria-label="{e(ad)} sayfamız">{ikon[k]()}<span>{e(ad)}</span></a>'
        for ad, u, k in D.SOSYAL)

def alt_bilgi():
    ilce_ln = " · ".join(
        f'<a href="/{i["slug"]}-iskele-kiralama/">{e(i["ad"])}</a>' for i in D.ILCELER)
    # ⚠️ 18 tür alt alta footer'ı aşırı uzatıyordu (ekran görüntüsünde kesiliyordu).
    #    İlk 9 + "tümü" bağlantısı; tam liste /iskele-cesitleri/ sayfasında.
    tur_ln = "".join(f'<li><a href="/{t["slug"]}/">{e(t["ad"])}</a></li>' for t in D.TURLER[:9])
    tur_ln += '<li class="alt-tumu"><a href="/iskele-cesitleri/">Tüm iskele çeşitleri →</a></li>' 
    reh_ln = "".join(f'<li><a href="/{r["slug"]}/">{e(r["ad"])}</a></li>' for r in D.REHBERLER)
    return f"""<footer class="alt">
  <div class="kap">
    <div class="alt-ust">
      <div class="alt-marka">
        <a class="logo-bag" href="/">{logo(buyuk=True)}</a>
        <p>{e(S['aciklama'])}</p>
        {tel_btn("dg dg-sari")}
        <p class="alt-pdf">{tanitim_pdf_bag("alt-pdf-bag")}</p>
      </div>
      <div class="alt-sut"><h3>İskele Türleri</h3><ul>{tur_ln}</ul></div>
      <div class="alt-sut"><h3>Rehberler</h3><ul>{reh_ln}</ul></div>
      <div class="alt-sut alt-iletisim"><h3>İletişim</h3>
        <p class="adres">{e(S['adres'])}</p>
        <p><a href="tel:{S['tel_link']}">{e(S['tel'])}</a><br>
           <a href="tel:{S['tel2_link']}">{e(S['tel2'])}</a></p>
        <p class="alt-saat"><strong>{e(S['saat'])}</strong><br>
           <span>{e(S['saat_gun'])} · acil durumlarda 7/24</span></p>
        <p><a href="https://www.google.com/maps/search/?api=1&amp;query={e(S['adres'].replace(' ', '+'))}"
           target="_blank" rel="noopener">Yol tarifi al</a></p>
        <div class="alt-sosyal">{sosyal_baglantilar()}</div>
      </div>
    </div>
    <div class="alt-ilceler"><h3>İstanbul'un tüm ilçelerinde iskele kiralama</h3>
      <p class="ilce-agi">{ilce_ln}</p></div>
    <div class="alt-son">
      <p>&copy; 2026 {e(S['marka'])} · Tüm hakları saklıdır.</p>
      {w4_kredi()}
    </div>
  </div>
</footer>
<nav class="sabit-ara" aria-label="Hızlı iletişim">
  <a class="sa sa-tel" href="tel:{S['tel_link']}">
    <span class="sa-ik">{svg_tel()}</span><span class="sa-yz">Hat (1)</span></a>
  <a class="sa sa-tel" href="tel:{S['tel2_link']}">
    <span class="sa-ik">{svg_tel()}</span><span class="sa-yz">Hat (2)</span></a>
  <a class="sa sa-wa" href="https://wa.me/{S['wa']}" target="_blank" rel="noopener">
    <span class="sa-ik">{svg_wa()}</span><span class="sa-yz">WhatsApp</span></a>
</nav>
<script src="{surum('/assets/app.js')}" defer></script>
</body>
</html>
"""


# ── Görsel vitrini ──────────────────────────────────────────────────────────
# Kullanıcı 2026-09-01: "tam boy olarak yay, tıklanınca aranabilir olsun".
# ⚠️ KIRPMA YOK — object-fit:cover kullanılmıyor, görsel kendi oranında basılıyor
#    (kaynaklar 1:1 ile 1.87:1 arasında değişiyor; kırpmak kompozisyonu bozuyor).
# ⚠️ Görselin TAMAMI tel: bağlantısı.
def vitrin(taban, oncelik=False, yazi=None, sinif=""):
    if not taban or not gorsel_var(taban):
        return ""
    alt = D.GORSEL_ALT.get(taban, S["marka"] + " iskele kiralama")
    g = gorsel(taban, alt, boy="(min-width:1000px) 980px, 100vw", oncelik=oncelik)
    if not g:
        return ""
    etiket = yazi or "Hemen ara: " + S["tel"]
    return (f'<a class="{("vitrin " + sinif).strip()}" href="tel:{S["tel_link"]}" '
            f'aria-label="{e(alt)} — {e(etiket)}">{g}'
            f'<span class="vitrin-ara">{svg_tel()}<span>{e(etiket)}</span></span></a>')

def ilce_gorseli(i, sira=0):
    """İlçe sayfalarında havuzdan dönüşümlü görsel — her ilçe farklı görselle açılıyor."""
    h = D.GENEL_HAVUZ
    return h[(D.ILCELER.index(i) + sira) % len(h)]

# ── JSON-LD ─────────────────────────────────────────────────────────────────
def ldj(nesne):
    return ('<script type="application/ld+json">' +
            json.dumps(nesne, ensure_ascii=False, separators=(",", ":")) + '</script>')

def isletme_semasi(alan_adi=None):
    """⚠️ aggregateRating BİLİNÇLİ olarak YOK — gerçek doğrulanabilir değerlendirme
    verisi olmadan puan işaretlemesi yapılmaz (emsal: web4medya google-reklam-uzmani)."""
    n = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "@id": ALAN + "/#isletme",
        "name": S["marka"],
        "url": ALAN + "/",
        "telephone": [S["tel_link"], S["tel2_link"]],
        "description": S["aciklama"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": S["adres_sokak"],
            "addressLocality": S["adres_ilce"],
            "addressRegion": "İstanbul",
            "postalCode": S["adres_pk"],
            "addressCountry": "TR",
        },
        "areaServed": {"@type": "City", "name": "İstanbul"},
        "sameAs": [u for _, u, _ in D.SOSYAL],
        "openingHours": S["saat_schema"],
        "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday",
                          "Friday", "Saturday", "Sunday"],
            "opens": "08:30", "closes": "19:00",
        },
        "geo": {"@type": "GeoCoordinates",
                "latitude": D.GEO["lat"], "longitude": D.GEO["lon"]},
        "hasMap": D.HARITA_LINK,
    }
    if alan_adi:
        n["areaServed"] = {"@type": "AdministrativeArea", "name": alan_adi + ", İstanbul"}
    return ldj(n)

def sss_semasi(sorular):
    return ldj({"@context": "https://schema.org", "@type": "FAQPage",
                "mainEntity": [{"@type": "Question", "name": s,
                                "acceptedAnswer": {"@type": "Answer", "text": c}}
                               for s, c in sorular]})

# ── Bileşenler ──────────────────────────────────────────────────────────────

def dalga(ters=False):
    """Hero altındaki dalgalı ayraç — saf SVG, tek yol, ~0,3 KB."""
    s = "dalga dalga-ters" if ters else "dalga"
    return (f'<div class="{s}" aria-hidden="true">'
            f'<svg viewBox="0 0 1440 90" width="1440" height="90" preserveAspectRatio="none">'
            f'<path d="M0,54 C240,90 480,10 720,32 C960,54 1200,86 1440,58 L1440,90 L0,90 Z"/>'
            f'</svg></div>')

def hero_h1(satirlar):
    # ⚠️ Satırlar arasına boşluk şart: bloklar görsel olarak alt alta ama metin
    #    çıkarımında bitişiyor ("kurarız,siz işinize bakın") — Google da böyle okuyor.
    return ('<h1 class="hb">' +
            " ".join(f'<span class="l"><span>{e(s)}</span></span>' for s in satirlar) +
            '</h1>')

def guven_seridi():
    """⚠️ Buradaki maddeler data.ONAYLI_IDDIALAR ile sınırlı; kullanıcı onayı olmadan
    'sigortalı', '20 yıl tecrübe', '7/24' gibi iddia EKLEME."""
    ogeler = [
        ("10 yılı aşkın deneyim", "İstanbul'da köklü bir saha geçmişi"),
        ("İstanbul'un tüm ilçeleri", "Avrupa ve Anadolu yakasının tamamına kurulum"),
        ("Her gün 08:30 – 19:00", "Pazar dahil açığız; acil durumlarda 7/24 ulaşabilirsiniz"),
        ("Kurulum, söküm ve sigorta", "İskeleyi biz kurar, biz sökeriz; süreç sigorta güvencesinde"),
    ]
    ic = "".join(f'<li><strong>{e(a)}</strong><span>{e(b)}</span></li>' for a, b in ogeler)
    # ⚠️ Dalga ayracı burada, koyu bloğun SONUNDA. Önceden hero'nun altındaydı ve
    #    dolgusu (açık gri) ile ardından gelen koyu şerit arasında gereksiz açık bir
    #    bant oluşuyordu — kullanıcı "ortada beyaz çizgi" diye bildirdi.
    #    Dalga dolgusu daima BİR SONRAKİ bölümün rengiyle aynı olmalı.
    return (f'<section class="serit"><div class="kap"><ul>{ic}</ul></div>'
            f'{dalga()}</section>')

def sss_bolum(sorular, baslik="Sık Sorulan Sorular"):
    ic = "".join(
        f'<details class="sss-o"><summary>{e(s)}</summary><div class="sss-c"><p>{c}</p></div></details>'
        for s, c in sorular)
    return (f'<section class="bol sss"><div class="kap dar">'
            f'<h2>{e(baslik)}</h2>{ic}</div></section>')

def cta_band(baslik, metin):
    return f"""<section class="cta"><div class="kap dar">
  <h2>{e(baslik)}</h2><p>{e(metin)}</p>
  <div class="dg-grup">{tel_btn()}{tel2_btn()}{wa_btn()}</div>
</div></section>"""


def kiralama_donemleri():
    """Firma tanıtım PDF'indeki "Esnek Kiralama Dönemleri" bölümü.
    ⚠️ Saatlik kiralama YOK — ne PDF'te ne de teyitli iddialarda geçiyor."""
    kart = "".join(
        f'<div class="donem"><h3>{e(a)}</h3><p>{e(b)}</p></div>'
        for a, b in D.KIRALAMA_DONEMLERI)
    return f"""<section class="bol donemler"><div class="kap">
  <h2>Kiralama Süresi İşinize Göre</h2>
  <p class="giris">Her iş aynı sürmüyor; kiralama dönemini de ona göre seçiyoruz.
     Ne kadar süreceğini söyleyin, en ekonomik olanı birlikte belirleyelim.</p>
  <div class="izgara-3">{kart}</div>
</div></section>"""

def tanitim_pdf_bag(sinif="dg dg-hat2"):
    """Firma tanıtım dosyası. ⚠️ 2,6 MB — yeni sekmede açılıyor, otomatik inmiyor."""
    return (f'<a class="{sinif}" href="{D.TANITIM_PDF}" target="_blank" rel="noopener">'
            f'<span>Firma tanıtım dosyası (PDF, {D.TANITIM_PDF_BOYUT})</span></a>')

def hesaplayici():
    """Cephe metrekaresi hesabı. ⚠️ TL basmaz — fiyat listesi henüz onaylanmadı
    (data.FIYATLAR boş). Fiyat gelince buraya tutar satırı eklenecek."""
    return """<section class="bol hesap" id="hesap"><div class="kap dar">
  <h2>Cephe Metrekaresi Hesaplayıcı</h2>
  <p class="giris">İskele kirası cephe metrekaresi üzerinden konuşulur. Binanızın bir cephesinin
     enini ve kat sayısını girin; kaç metrekare iskele gerektiğini kabaca görün. Kesin rakam
     keşifte, gerçek ölçüyle çıkar.</p>
  <div class="hesap-kutu">
    <label>Cephe eni (metre)
      <input type="number" id="h-en" min="1" max="200" step="0.5" value="12" inputmode="decimal"></label>
    <label>Kat sayısı
      <input type="number" id="h-kat" min="1" max="30" step="1" value="5" inputmode="numeric"></label>
    <label>Kat yüksekliği (metre)
      <input type="number" id="h-yuk" min="2" max="6" step="0.1" value="2.9" inputmode="decimal"></label>
    <div class="hesap-sonuc" id="h-sonuc" aria-live="polite"></div>
  </div>
  <p class="not">Hesap yaklaşıktır: çatı üstü çıkma, balkon, giriş saçağı ve zemin kotu farkı
     metrekareyi değiştirir. Birden fazla cephe kurulacaksa her cepheyi ayrı hesaplayıp toplayın.</p>
  <div class="dg-grup">{ara}</div>
</div></section>""".replace("{ara}", tel_btn(metin="Ölçüyle birlikte arayın: " + S["tel"]))

def tur_kartlari(baslik="İskele Türleri", haric=None, giris=None):
    """Referans kurumsal düzendeki yuvarlak görselli hizmet kartı.
    ⚠️ Görsel <picture> içinde; .kart-daire'ye aspect-ratio + overflow verildi,
       img'e object-fit:cover — burada kırpma İSTENİYOR (daire içine oturması için),
       vitrin() görsellerindeki 'kırpma yok' kuralı bunun dışında."""
    kart = []
    for t in D.TURLER:
        if t["slug"] == haric:
            continue
        g = gorsel(D.TUR_GORSEL.get(t["slug"], ""), D.GORSEL_ALT.get(D.TUR_GORSEL.get(t["slug"], ""), t["ad"]),
                   boy="(min-width:1000px) 280px, 45vw")
        daire = f'<span class="kart-daire">{g}</span>' if g else ""
        kart.append(
            f'<a class="kart gel gel-3b" href="/{t["slug"]}/">'
            f'{daire}<span class="kart-ic"><h3>{e(t["ad"])}</h3><p>{e(t["ozet"])}</p>'
            f'<span class="kart-ok">Detaylı Bilgi</span></span></a>')
    gr = f'<p class="giris">{e(giris)}</p>' if giris else ""
    return (f'<section class="bol turler"><div class="kap"><div class="bol-bas">'
            f'<h2>{e(baslik)}</h2>{gr}</div>'
            f'<div class="izgara izgara-kart">{"".join(kart)}</div></div></section>')

def ilce_agi(baslik="İstanbul'un Tüm İlçelerinde İskele Kiralama", haric=None):
    """39 ilçeye giden bağlantı ağı. Anasayfada yaka yaka gruplanır."""
    bol = []
    for yaka in ("Avrupa", "Anadolu"):
        ln = "".join(
            f'<li><a href="/{i["slug"]}-iskele-kiralama/">{e(i["ad"])}</a></li>'
            for i in D.ILCELER if i["yaka"] == yaka and i["slug"] != haric)
        bol.append(f'<div class="yaka"><h3>{yaka} Yakası</h3><ul class="ilce-liste">{ln}</ul></div>')
    return (f'<section class="bol ilceler" id="ilceler"><div class="kap"><h2>{e(baslik)}</h2>'
            f'<p class="giris">Merkezimiz {e(S["merkez_ilce"])}; kurulum ekibi İstanbul\'un iki '
            f'yakasına da aynı depodan çıkıyor. İlçenize ait sayfada o bölgedeki yapı stoğu ve '
            f'kurulum şartlarıyla ilgili notları bulabilirsiniz.</p>'
            f'<div class="yakalar">{"".join(bol)}</div></div></section>')


# ── Anasayfaya iç linkleme ──────────────────────────────────────────────────
# Kullanıcı 2026-09-01'de istedi: her iç sayfadan anasayfaya, bu 5 kelimeden biriyle.
# ⚠️ 52 sayfanın hepsinde AYNI anchor kullanılmıyor — tek tip tam eşleşme site
#    genelinde aşırı optimizasyon sinyali üretir. Kelimeler sayfa sırasına göre
#    dönüşümlü dağıtılıyor, her biri ~10 sayfada geçiyor.
ANA_ANCHOR = [
    "İstanbul iskele kiralama",
    "kiralık iskele İstanbul",
    "İstanbul iskele fiyatları",
    "iskele kiralama İstanbul",
    "İstanbul kiralık iskele",
]
_anchor_sayac = {"n": 0}
def ana_link(kalip=None):
    """Anasayfaya giden anchor'lı bağlantı; her çağrıda sıradaki kelimeyi kullanır."""
    k = ANA_ANCHOR[_anchor_sayac["n"] % len(ANA_ANCHOR)]
    _anchor_sayac["n"] += 1
    bag = '<a href="/">%s</a>' % k
    return (kalip % bag) if kalip else bag


def harita_bolum(ilce=None):
    """⚠️ Facade: iframe DOM'a ancak tıklanınca giriyor. Böylece Google Maps'in
    ağır JS'i ilk açılış ağırlığına hiç girmiyor — 40 sayfada durması bedava."""
    baslik = "Merkezimiz" if not ilce else f"{ek(ilce, 'dat')} Nereden Geliyoruz?"
    giris = S["adres"] if not ilce else (merkez_cumlesi(ilce) + " Depo adresimiz: " + S["adres"])
    return f"""<section class="bol harita-bol" id="iletisim"><div class="kap dar">
  <h2>{e(baslik)}</h2>
  <p class="giris">{e(giris)}</p>
  <div class="harita">
    <iframe src="{e(D.HARITA_EMBED)}" title="Deha İskele konumu — Google Haritalar"
      loading="lazy" referrerpolicy="strict-origin-when-cross-origin"
      allowfullscreen></iframe>
  </div>
  <div class="dg-grup">
    <a class="dg dg-sari" href="{e(D.HARITA_LINK)}" target="_blank" rel="noopener">Yol tarifi al</a>
    {tel_btn("dg dg-wa")}
  </div>
</div></section>"""


# ── H2 → içerik eşleştirici ──────────────────────────────────────────────────
# Kullanıcının verdiği 307 H2 başlığının her biri, anahtar kelimesine göre bir
# içerik bloğuna bağlanıyor. İlçeye özgü bloklar doku/vurgu/mahalle verisinden
# besleniyor; genel bloklar ilgili tür/rehber sayfasına link veriyor.
# ⚠️ Metin kullanıcının kendi dilinde (samimi, 1. şahıs, dürüst uyarı) —
#    bkz feedback_web4medya_kullanici_dili.
def h2_govde(b, i):
    ad = i["ad"]
    d = b.lower()
    def has(*k): return any(x in d for x in k)

    if has("fiyat", "ücret", "maliyet"):
        return (f"<p>Size en baştan dobra söyleyeyim: iskelenin sabit bir fiyat listesi yok :) "
                f"Rakam dört şeyden çıkıyor — cephenin kaç metrekare olduğu, iskelenin kaç ay "
                f"duracağı, kurulum-söküm işçiliği ve nakliye.</p>"
                f"<p>Metrekare hesabı basit: cephe eni × bina yüksekliği. Beş katlı, 12 metre "
                f"enindeki bir cephe kabaca 170-180 m² ediyor.. Kendi ölçünüzü "
                f'<a href="/#hesap">hesaplayıcıdan</a> çıkarabilirsiniz. Ama {ad} için şunu da '
                f"ekleyeyim: aynı metrekarede bile sokak dar, zemin bozuk ya da bina yüksekse "
                f"işçilik değişiyor. Detayını "
                f'<a href="/iskele-kiralama-fiyatlari/">fiyat rehberinde</a> yazdım.</p>')

    if has("güvenlik", "yasal", "zorunluluk", "standart", "korkuluk", "ağlı", "sertifika", "kalite belgesi", "denetim"):
        return ("<p>Burada tercih diye bir şey yok, mevzuatın istediği asgari şartlar var. "
                "Korkuluk en az 100 cm, ara korkuluk ve en az 15 cm topuk levhası birlikte "
                "aranıyor; çalışma platformu 60 cm'den dar olamıyor. Dayanağı "
                "Yapı İşlerinde İş Sağlığı ve Güvenliği Yönetmeliği (RG 05.10.2013 / 28786).</p>"
                "<p>Size dürüst bir uyarı: iskelede en sık gördüğüm hata, \"malzeme geçmiyor\" "
                "diye korkuluğun sökülmesi. Lütfen yapmayın.. Bir şeyin yerinden oynaması "
                "gerekiyorsa bizi arayın, gelip biz düzenleyelim. Ayrıntısı "
                '<a href="/iskele-is-guvenligi/">iş güvenliği sayfasında</a>.</p>')

    if has("modüler", "sistem iskele", "endüstriyel", "kapasite", "ağır yük", "çelik"):
        return (f"<p>Modüler (sistem) iskele, dikmelerdeki rozetlere yatay ve çapraz elemanların "
                f"takılmasıyla kuruluyor. Avantajı şu: cephe düz değilse, çıkma-kademe varsa ya "
                f"da platformda ağır malzeme duracaksa çerçeve iskele zorlanıyor, modüler sistem "
                f"uyum sağlıyor.</p>"
                f"<p>Ama her işe modüler gerekmiyor — düz ve alçak bir apartman cephesinde "
                f"gereksiz masraf olur, onu da söyleyeyim :) Karşılaştırmasını "
                f'<a href="/sistem-iskele/">sistem iskele sayfasında</a> yaptım.</p>')

    if has("mobil", "hafif", "dar alan", "katlanır", "iç mekân", "seyyar", "kule"):
        return (f"<p>Nokta işler ve iç mekân için kule (seyyar) iskele kullanıyoruz — tekerlekli "
                f"olduğu için iterek yer değiştiriyor. {ek(i)} dar sokaklarda ve tek duvarlık "
                f"işlerde tüm cepheyi kurmaya gerek kalmıyor, bu da doğrudan maliyetten düşüyor.</p>"
                f"<p>İki kuralı var, ikisini de ciddiye alın: tekerlekler frenlenmeden platforma "
                f"çıkılmaz ve <strong>üzerinde insan varken kule asla itilmez</strong>. "
                f'Ayrıntısı <a href="/kule-iskele/">kule iskele sayfasında</a>.</p>')

    if has("restorasyon", "tarihi", "hassas"):
        return (f"<p>Tarihi yapıda iş, normal cepheden ayrı bir hikâye. Sokak çoğu zaman dar, "
                f"izin süreci uzun ve cepheye zarar vermeden çalışmak gerekiyor. İskelenin yere "
                f"basan ayak izini daraltıp yukarıda konsolla açılıyoruz.</p>"
                f"<p>Şunu baştan söyleyeyim: koruma alanındaki binalarda izin çıkmadan tek boru "
                f"dikmiyoruz. İzin süreci bazen işin kendisinden uzun sürüyor.. ama başka yolu yok.</p>")

    if has("boyama", "boya", "yenileme", "tadilat", "cephe temizliği"):
        return (f"<p>{ek(i)} en sık gelen iş bu: dış cephe boyası, sıva onarımı, cephe temizliği. "
                f"Bu işlerde iskele uzun durmuyor, o yüzden kurulum-söküm hızı toplam maliyette "
                f"kiradan bile önemli olabiliyor.</p>"
                f"<p>Boya sıçramasına karşı file gerilecekse baştan söyleyin — file rüzgâr yükünü "
                f"ciddi artırıyor, cepheye bağlantıyı ona göre sıklaştırıyoruz. "
                f'<a href="/boya-badana-iskelesi/">Boya iskelesi sayfasında</a> detaylandırdım.</p>')

    if has("teslimat", "montaj", "kurulum", "söküm", "iade", "nakliye", "teslim", "ekip", "süre"):
        return (f"<p>Süreç şöyle işliyor: arayın, kat sayısı ve cephe enini söyleyin — telefonda "
                f"aralık verelim. Sonra keşfe geliyoruz; cepheyi ölçüyor, zemini ve aracın "
                f"yanaşacağı yeri görüyoruz. {merkez_cumlesi(i)}</p>"
                f"<p>Kurulum günü ekip sabah geliyor. Normal bir apartman cephesinde iş çoğunlukla "
                f"bir günde bitiyor; yüksek blokta ya da dar sokakta uzayabiliyor. İş bittiğinde "
                f"sökümü de biz yapıyoruz, malzeme sizde kalmıyor. "
                f'Adım adım <a href="/iskele-kurulum-sokum-sureci/">süreç sayfasında</a>.</p>')

    if has("sözleşme", "hasar", "sorumluluk", "destek", "yedek parça", "bakım", "kontrol süreci"):
        return ("<p>İskeleyi biz kuruyoruz, kurulum bitince teslim kontrolü yapıyoruz: korkuluklar, "
                "platformlar, topuk levhaları ve cephe bağlantıları tek tek gözden geçiriliyor. "
                "İskele ondan sonra teslim ediliyor.</p>"
                "<p>Kullanım süresince iskelede değişiklik yapılmaması gerekiyor. Bir parça "
                "söküldüyse ya da bir yer gevşediyse haber verin — geliyoruz, yerine takıyoruz. "
                "Bunun için ayrıca bir şey istemiyoruz, işin parçası :)</p>")

    if has("kısa", "uzun dönem", "aylık", "vadeli", "süreli"):
        return (f"<p>Kiralama süresini işinize göre ayarlıyoruz: günlük, haftalık ve aylık "
                f"seçeneklerimiz var. {ek(i)} dış cephe boyası çoğu zaman birkaç haftada "
                f"bitiyor; mantolama, sıva yenileme ve güçlendirme işleri aylara yayılıyor.</p>"
                f"<p>Tavsiyem: süreyi olduğundan kısa söylemeyin. \"İki haftada biter\" deyip "
                f"iki ay süren çok iş gördüm.. İşin gerçek takvimini baştan konuşursak hesap da "
                f"sonradan şaşmıyor.</p>")

    if has("yüksek kat", "yüksek katlı", "cephe iskelesi", "çok katlı", "kule iskele planlama"):
        return (f"<p>Yükseklik arttıkça iş değişiyor. Belirli bir kat sayısına kadar klasik "
                f"çerçeve iskele hem yeterli hem ekonomik; ondan sonra hem malzeme hem süre "
                f"büyüyor ve sistem iskele ya da çatıdan askıya alınan platform daha mantıklı "
                f"oluyor.</p>"
                f"<p>Bu yüzden telefonda ilk sorduğum şey kat sayısı oluyor. "
                f'<a href="/cephe-iskelesi/">Cephe iskelesi</a> ve '
                f'<a href="/asma-iskele/">asma iskele</a> sayfalarında ikisini '
                f"karşılaştırdım.</p>")

    if has("firma nasıl seçilir", "güvenilir", "seçimi", "hangi iskele"):
        return (f"<p>Size iskeleci seçerken bakmanız gereken üç şeyi söyleyeyim :) Birincisi: "
                f"ölçü almadan telefonda kesin fiyat veriyorsa dikkatli olun — o rakam keşiften "
                f"sonra değişir. İkincisi: kurulumu kim yapıyor? Malzemeyi bırakıp giden değil, "
                f"kuran ve sökene bakın.</p>"
                f"<p>Üçüncüsü ve en önemlisi: korkuluk, topuk levhası ve bağlantı konusunda ne "
                f"diyor? Bunları \"gerekirse takarız\" diyen biriyle çalışmayın. İskele "
                f"üzerinde insan çalışan bir yapı, orada pazarlık olmaz.</p>")

    # ilçe adı geçen ve yukarıdakilere girmeyen başlıklar → saha bloğu
    return (f"<p>{ek(i, 'gen')} yapı stoğu ağırlıklı olarak {i['doku']}. İskele işi de buna göre "
            f"şekilleniyor; aynı ölçüdeki iki bina, sokağı ve zemini farklı olduğu için aynı "
            f"kurulumu istemiyor.</p>"
            f"<p>{i['vurgu']}.</p>")


def ilce_h3_blok(i):
    """⚠️ Kullanıcının ilk planındaki 10 tekrar eden H3 kalıbı yerine 4 gerçek başlık.
    Sebep: 39×10 = 390 başlığın %85'i aynı kalıptı; Google'ın 'ölçeklendirilmiş içeriği
    kötüye kullanma' ve kelime doldurma tarifine giriyordu. Kullanıcı 2026-09-01'de
    risk tablosunu görüp bu seçeneği seçti. ⛔ 10'lu kalıba geri dönme."""
    ad = i["ad"]
    return f"""
  <h3>{e(ek(i))} kısa süreli iskele kiralama</h3>
  <p>Tek duvar boyası, balkon onarımı, tabela montajı gibi işlerde iskele birkaç hafta duruyor.
     Böyle işlerde kurulum-söküm işçiliği toplam hesapta kiradan büyük çıkabiliyor; o yüzden
     \"aylık ne kadar?\" sorusu tek başına yetmiyor, ikisini birlikte konuşmak gerekiyor.</p>

  <h3>{e(ek(i))} günlük ve haftalık iskele kiralama</h3>
  <p>Her iş aylarca sürmüyor. Tek duvar boyası, balkon onarımı ya da acil bir tadilat için
     günlük kiralama en mantıklısı; orta vadeli işlerde haftalık seçenek devreye giriyor.
     Ne kadar süreceğini söyleyin, ona göre en ekonomik dönemi birlikte seçelim.</p>

  <h3>{e(ek(i))} aylık ve uzun dönem kiralama</h3>
  <p>Mantolama, sıva yenileme ve güçlendirme işlerinde iskele aylarca duruyor; bu işlerde aylık
     kiralama en ekonomiği oluyor. Uzun kirada iskeleyi düzenli kontrol ediyoruz — aylar süren
     şantiyede bu hem güvenlik hem denetim meselesi. Süre uzarsa yeni kurulum ücreti çıkmıyor.</p>

  <h3>{e(ek(i))} acil iskele ihtiyacı</h3>
  <p>Acil durumlarda önce takvime bakıyoruz ve size <strong>gerçek</strong> en yakın günü
     söylüyoruz. Burada dürüst olmayı tercih ediyorum: \"hemen geliriz\" deyip üç gün sonra
     gelmektense, baştan doğru günü söylemek daha iyi.. Siz de işinizi ona göre planlarsınız.</p>

  <h3>{e(ek(i))} tadilat ve iç mekân işleri</h3>
  <p>Her iş tüm cepheyi kurmayı gerektirmiyor. İç mekân tadilatı, yüksek tavanlı dükkan ya da
     depo işlerinde kule (seyyar) iskele yeterli oluyor ve çok daha ekonomik.
     Hangisinin işinize oturduğunu keşifte birlikte belirliyoruz.</p>
"""


def bolunmus_bolum():
    """Referans düzendeki turuncu/koyu split bölüm: solda öne çıkan sistemler,
    sağda firma anlatımı. Görseller lazy, animasyon yalnız transform/opacity."""
    one_cikan = [t for t in D.TURLER if t["slug"] in
                 ("cephe-iskelesi", "flansli-iskele", "mobil-iskele", "asma-iskele")]
    kart = []
    for t in one_cikan:
        g = gorsel(D.TUR_GORSEL.get(t["slug"], ""),
                   D.GORSEL_ALT.get(D.TUR_GORSEL.get(t["slug"], ""), t["ad"]),
                   boy="(min-width:1000px) 260px, 45vw")
        kart.append(f'<a class="urun" href="/{t["slug"]}/">{g}'
                    f'<span class="urun-ic"><h3>{e(t["ad"])}</h3>'
                    f'<span class="urun-ok">Detaylı Bilgi</span></span></a>')
    return f"""<section class="bolunmus">
  <div class="kap bolunmus-ic">
    <div class="bl-sol">
      <h2>Öne Çıkan Sistemlerimiz</h2>
      <p>En sık kurduğumuz dört sistem. Tamamı için iskele çeşitleri sayfasına bakın.</p>
      <div class="urunler">{"".join(kart)}</div>
      <a class="dg dg-cerceve" href="/iskele-cesitleri/"><span>18 sistemin tamamı</span></a>
    </div>
    <div class="bl-sag">
      <h2>Güvenle Yükselen İskele</h2>
      <p>Deha İskele olarak <strong>10 yılı aşkın sektör deneyimiyle</strong> İstanbul
         genelinde iskele kiralıyoruz. Depomuz Eyüpsultan'da; ekip Avrupa ve Anadolu
         yakasına aynı yerden çıkıyor.</p>
      <p>Bu işte uzun süre kalmanın bir avantajı var: aynı ölçüdeki iki binanın neden aynı
         kurulumu istemediğini artık keşfe gitmeden tahmin edebiliyoruz :) Dar sokak, eğimli
         bahçe, bitişik nizam, otopark üstü zemin — her biri iskeleyi baştan değiştiriyor.
         O yüzden telefonda kesin fiyat vermek yerine gelip bakmayı tercih ediyoruz.</p>
      <p>Kurulum da söküm de bize ait, süreç sigorta güvencesinde. Her gün
         <strong>08:30 – 19:00</strong> arası açığız; acil durumlarda saat fark etmeksizin
         ulaşabilirsiniz.</p>
      <div class="dg-grup">
        <a class="dg dg-cerceve-ak" href="/hakkimizda/"><span>Bizi Tanıyın</span></a>
        {teklif_btn("dg dg-sari")}
      </div>
    </div>
  </div>
</section>"""


# ── Anasayfa SEO içeriği ────────────────────────────────────────────────────
# Kullanıcı 2026-09-01: anasayfa şu başlıklarla zenginleşsin — "İstanbul'da iskele
# nerede kiralanır?", "İskele kiralama şartları", "İskele teslim süreci",
# "İstanbul kurumsal iskele kiralama firması: Deha İskele".
# ⚠️ "Aynı gün teslim" iddiası kullanıcının kendi yazdığı metinden geliyor (teyitli).
# ⛔ Depozito/sözleşme şartları YAZILMADI — teyit edilmedi.
def seo_icerik():
    ilce_ln = " · ".join(
        f'<a href="{ilce_yolu(i)}">{e(i["ad"])}</a>'
        for i in D.ILCELER if i["slug"] in
        ("esenyurt", "bagcilar", "kadikoy", "umraniye", "basaksehir", "maltepe", "fatih", "sisli"))
    return f"""<section class="bol metin-bol"><div class="kap dar metin">

  <h2>İstanbul'da İskele Nerede Kiralanır?</h2>
  <p>En kısa cevabı vereyim: bizden :) Deha İskele olarak depomuz
     <strong>{e(S['adres_ilce'])}</strong>'da ve İstanbul'un <a href="/ilceler/">39 ilçesinin
     tamamına</a> kurulum yapıyoruz. Ekip Avrupa ve Anadolu yakasına aynı noktadan çıkıyor;
     yani hangi ilçede olursanız olun aynı ekiple çalışıyorsunuz.</p>
  <p>İskele kiralarken bakmanız gereken üç şeyi söyleyeyim. Birincisi: firma kurulumu ve
     sökümü kendisi yapıyor mu, yoksa malzemeyi kapınıza bırakıp gidiyor mu? İkincisi:
     ölçü almadan telefonda kesin fiyat veriyor mu? Veriyorsa o rakam keşiften sonra
     değişir.. Üçüncüsü ve en önemlisi: korkuluk, topuk levhası ve cephe bağlantısı
     konusunda ne diyor? Bunları "gerekirse takarız" diyen biriyle çalışmayın.</p>
  <p>Sık çalıştığımız ilçelerden birkaçı: {ilce_ln} — ilçenize ait sayfada o bölgede
     karşılaştığımız zemin, sokak ve yapı stoğu notlarını da yazdık.</p>

  <h2>İskele Kiralama Şartları</h2>
  <p>Şartlarımızı olabildiğince sade tuttuk, sürpriz sevmiyoruz:</p>
  <ul class="ok-liste">
    <li><strong>Keşif ücretsiz.</strong> Gelip cepheyi ölçüyoruz, zemini ve aracın
        yanaşacağı yeri görüyoruz. Bu olmadan kesin fiyat çıkmıyor.</li>
    <li><strong>Süre size bağlı.</strong> Günlük, haftalık ve aylık kiralama var;
        ihtiyaç duyduğunuz süre boyunca iskele sizde kalıyor. Süre uzarsa yeni bir
        kurulum ücreti çıkmıyor.</li>
    <li><strong>Kurulum ve söküm bize ait.</strong> Malzemeyi bırakıp gitmiyoruz;
        iş bitince toplayıp götürüyoruz. Depolama, taşıma ve bakım sizin derdiniz olmuyor.</li>
    <li><strong>Süreç sigorta güvencesinde.</strong> Kiralama boyunca kapsamlı sigorta
        kapsamıyla çalışıyoruz.</li>
    <li><strong>İskelede değişiklik yapılmaz.</strong> Korkuluğun sökülmesi ya da
        platformun kaydırılması iskelenin taşıma ve devrilme davranışını değiştiriyor.
        Bir şeyin yerinden oynaması gerekiyorsa bizi arayın, gelip biz düzenleyelim.</li>
    <li><strong>Ölçü değişirse fiyat da değişir.</strong> Keşifte konuşulan cepheye ek
        bir yüzey çıkarsa bunu baştan söylüyoruz — iş ortasında sürpriz kalem çıkmıyor.</li>
  </ul>
  <p>Mevzuatın aradığı asgari şartları (korkuluk yüksekliği, topuk levhası, platform
     genişliği) <a href="/iskele-is-guvenligi/">iş güvenliği sayfasında</a> Resmî Gazete
     referanslarıyla yazdım; merak ederseniz kaynağından okuyabilirsiniz.</p>

  <h2>İskele Teslim Süreci</h2>
  <p>Süreç bir telefonla başlıyor, sökümle bitiyor. Arada altı adım var:</p>
  <ol class="adim">
    <li><strong>Arayın, kabaca anlatın.</strong> Kat sayısı ve cephe eni yeterli;
        telefonda size bir aralık verebiliyorum.</li>
    <li><strong>Ücretsiz keşif.</strong> Cepheyi ölçüyor, zemini ve aracın yanaşacağı
        yeri görüyoruz. Balkon, çıkma, saçak ve kot farkı hep burada ortaya çıkıyor.</li>
    <li><strong>Net fiyat ve tarih.</strong> Metrekare, süre ve işçilik netleşince
        rakamı ve teslim gününü söylüyoruz.</li>
    <li><strong>Teslimat ve kurulum.</strong> Malzeme sahaya geliyor, zemin hazırlanıyor,
        iskele kat kat yükseliyor. Cepheye bağlantılar yapılmadan üst kata çıkılmıyor.
        Normal bir apartman cephesinde iş çoğunlukla bir günde bitiyor.</li>
    <li><strong>Teslim kontrolü.</strong> Korkuluk, platform, topuk levhası ve bağlantılar
        tek tek gözden geçiriliyor. İskele ondan sonra sizin.</li>
    <li><strong>Söküm.</strong> İş bitince bir telefon yeterli; sökümü biz yapıyor,
        alanı temiz bırakıyoruz.</li>
  </ol>
  <p>Sürecin tamamını adım adım <a href="/iskele-kurulum-sokum-sureci/">kurulum ve söküm
     rehberinde</a> anlattım.</p>

  <h2>İstanbul Kurumsal İskele Kiralama Firması: Deha İskele</h2>
  <p><strong>Çeşitli iskele türleriyle aynı gün içinde teslim hizmeti sunuyoruz.</strong>
     İhtiyaç duyduğunuz süre boyunca iskele kiralayabilirsiniz. Kurulum ve söküm
     aşamalarında ise her an yanınızdayız!</p>
  <p>10 yılı aşkın süredir bu işin içindeyiz. Bu sürede apartman cephesinden fabrika
     bakımına, tarihi yapı restorasyonundan etkinlik sahnesine kadar çok farklı iş gördük.
     <a href="/iskele-cesitleri/">18 farklı iskele sistemi</a> kiralıyoruz — cepheden
     kalıp altına, mobilden asma iskeleye kadar. Hangisinin sizin işinize oturduğundan
     emin değilseniz hiç uğraşmayın, arayın; keşifte binayı görüp birlikte karar veriyoruz.</p>
  <p>Her gün <strong>{e(S['saat'])}</strong> arası açığız, Pazar dahil; acil durumlarda
     saat fark etmeksizin ulaşabilirsiniz. Firmamızı daha yakından tanımak isterseniz
     <a href="/hakkimizda/">hakkımızda sayfamıza</a> bakabilir ya da doğrudan
     <a href="tel:{S['tel_link']}">{e(S['tel'])}</a> numarasından arayabilirsiniz.</p>
</div></section>"""


# ── Tanıtım videosu ─────────────────────────────────────────────────────────
# ⚠️ preload="none" + poster: 5 MB'lık dosya ilk yükte İNMİYOR, ancak oynat'a
#    basılınca geliyor. ⛔ preload="auto"/"metadata" yapma, sayfa hızını bozar.
def video_bolum(baslik="İskele Kiralama Hizmetimiz"):
    v = D.VIDEO
    poster = ""
    if gorsel_var(v["poster"]):
        poster = f'/images/w900/{v["poster"]}.webp'
    sema = ldj({
        "@context": "https://schema.org", "@type": "VideoObject",
        "name": v["ad"], "description": v["aciklama"],
        "thumbnailUrl": ALAN + poster if poster else ALAN + "/images/logo-512.png",
        "uploadDate": v["tarih"], "duration": v["sure_iso"],
        "contentUrl": ALAN + v["yol"],
        "publisher": {"@id": ALAN + "/#isletme"},
    })
    return f"""<section class="bol video-bol"><div class="kap">
  <div class="bol-bas">
    <h2>{e(baslik)}</h2>
    <p class="giris">İstanbul genelinde nasıl çalıştığımızı kısa bir videoda anlattık —
       keşiften kuruluma, kurulumdan sökme kadar.</p>
  </div>
  <div class="video-kutu">
    <video controls preload="none"{f' poster="{poster}"' if poster else ''}
      width="{v['genislik']}" height="{v['yukseklik']}"
      aria-label="{e(v['ad'])}">
      <source src="{e(v['yol'])}" type="video/mp4">
      Tarayıcınız video oynatmayı desteklemiyor.
      <a href="{e(v['yol'])}">Videoyu indirin</a>.
    </video>
  </div>
  <p class="video-not">İstanbul'da iskele kiralama için güvenilir ve kurumsal firma olan
     <strong>Deha İskele</strong>'yi tercih edebilirsiniz. Kaliteli ve sigortalı iskele
     ürünleriyle hangi alanda ihtiyaç duyarsanız duyun, bir telefonla iskelenizi ayağınıza
     kadar getiririz...</p>
  <div class="dg-grup video-dg">{tel_btn()}{wa_btn()}</div>
</div></section>{sema}"""

# ── İlçe sayfası ────────────────────────────────────────────────────────────
def ilce_yolu(i):
    return f'/{i["slug"]}-iskele-kiralama/'

def ilce_sss(i):
    ad = i["ad"]
    m = ", ".join(i["mahalle"][:3])
    return [
        (f"{ek(i)} iskele kiralama fiyatı nasıl belirleniyor?",
         "Fiyat üç şeyden çıkıyor: cephe metrekaresi, iskelenin kaç ay duracağı ve kurulum-söküm "
         "işçiliği. Metrekare, cephe eni ile bina yüksekliğinin çarpımı. Telefonda kat sayısını ve "
         "cephe enini söylerseniz aralık verebiliriz; kesin rakam için keşfe geliyoruz, çünkü "
         "balkon, çıkma ve zemin kotu ölçüyü değiştiriyor."),
        (f"{ek(i)} keşif ücretli mi?",
         "Keşifte cepheyi ölçüyoruz, zemini ve aracın yanaşacağı yeri görüyoruz. Ölçü almadan "
         "verilen rakam ya size fazla ya bize eksik geliyor; o yüzden önce yerinde bakıyoruz."),
        (f"{ek(i)} iskele ne kadar sürede kuruluyor?",
         # ⚠️ .capitalize() KULLANMA: tüm metni küçültüyor ve "İskelenin" → "i̇skelenin"
         #    oluyor (Python'un Türkçe bilmeyen lower'ı). Vurgu zaten büyük harfle başlıyor.
         f"{i['vurgu'].split(';')[0].strip()}. Normal bir apartman cephesinde kurulum "
         "çoğunlukla bir gün sürüyor; yüksek bloklarda ve zor erişimli sokaklarda bu süre uzayabiliyor. "
         "Kurulum gününü baştan söylüyoruz ki bina da kendi işini ona göre planlasın."),
        (f"İskele {ek(i)} ne kadar süre kalabilir?",
         "İstediğiniz kadar — günlük, haftalık ve aylık kiralama seçeneklerimiz var. Boya işi "
         "genelde birkaç haftada bitiyor, mantolama ve güçlendirme aylara yayılıyor. Süreyi "
         "baştan konuşuyoruz; uzarsa yeni kurulum ücreti çıkmadan devam ediyor."),
        (f"{m} taraflarına da geliyor musunuz?",
         f"Evet. {ek(i, 'gen')} tüm mahallelerine kurulum yapıyoruz. " + merkez_cumlesi(i)),
        ("İskele kurulduktan sonra sorumluluk kimde?",
         "İskeleyi biz kuruyoruz ve kurulum bittiğinde teslim kontrolü yapıyoruz. Kullanım "
         "süresince iskelede değişiklik yapılmaması, korkuluk ve platformların yerinden "
         "oynatılmaması gerekiyor. Bir şey söküldüyse haber verin, biz gelip yerine takalım."),
    ]

def ilce_sayfasi(i):
    ad, yol = i["ad"], ilce_yolu(i)
    komsular = [ILCE[k] for k in KOMSU.get(i["slug"], []) if k in ILCE]
    sorular = ilce_sss(i)
    baslik = f"{ad} İskele Kiralama ve Cephe İskelesi | {S['marka']}"
    aciklama = (f"{ad} genelinde cephe iskelesi kiralama, kurulum ve söküm. Keşifle net ölçü, "
                f"aylık kira, {S['merkez_ilce']} merkezli ekip. {S['tel']}")

    sema = (isletme_semasi(ad) + sss_semasi(sorular) +
            ldj({"@context": "https://schema.org", "@type": "Service",
                 "serviceType": "İskele kiralama",
                 "name": f"{ad} iskele kiralama",
                 "provider": {"@id": ALAN + "/#isletme"},
                 "areaServed": {"@type": "AdministrativeArea", "name": f"{ad}, İstanbul"},
                 "url": ALAN + yol}))

    mahalle_ln = ", ".join(i["mahalle"])
    ana_link_c = ana_link("Sadece %s değil, " + f"{ad} dışındaki tüm ilçelerde de "
                          "aynı ekiple çalışıyoruz; genel hizmet kapsamımızı ana sayfada "
                          "bulabilirsiniz.")
    komsu_ln = "".join(
        f'<li><a href="{ilce_yolu(k)}">{e(k["ad"])} iskele kiralama</a></li>' for k in komsular)

    # Yapı stoğuna göre tür önerisi — ilçe verisinden türetilir, elle yazılmaz.
    metin = " ".join([i["doku"], i["vurgu"]]).lower()
    oneri = []
    if any(x in metin for x in ("yüksek", "rezidans", "plaza", "kule", "on iki", "blok")):
        oneri.append(("sistem-iskele", "Yüksek ve uzun cepheler için sistem (modüler) iskele"))
        oneri.append(("asma-iskele", "Belirli bir katın üstünde cephe asansörü / askılı platform"))
    if any(x in metin for x in ("mantolama", "yalıtım", "güçlendirme", "dönüşüm")):
        oneri.append(("mantolama-iskelesi", "Isı yalıtımı işlerinde mantolama iskelesi"))
    if any(x in metin for x in ("boya", "sıva", "cephe")):
        oneri.append(("boya-badana-iskelesi", "Dış cephe boyası için kısa süreli cephe iskelesi"))
    if any(x in metin for x in ("depo", "fabrika", "imalathane", "sanayi", "tersane", "iç mekân")):
        oneri.append(("kule-iskele", "İç mekân ve nokta işler için kule (seyyar) iskele"))
    if not oneri:
        oneri.append(("cephe-iskelesi", "Apartman ve site cepheleri için standart cephe iskelesi"))
    gorulen, tekil = set(), []
    for s, a in oneri:
        if s not in gorulen:
            gorulen.add(s); tekil.append((s, a))
    oneri_ln = "".join(f'<li><a href="/{s}/">{e(a)}</a></li>' for s, a in tekil[:4])

    # Kullanıcının verdiği H2 planı → her başlık altına eşleşen içerik bloğu
    parcalar = []
    for n, b in enumerate(D.ILCE_H2[i["slug"]]):
        parcalar.append(f"\n  <h2>{e(b)}</h2>\n" + h2_govde(b, i))
        if n == 2:   # üçüncü H2'den sonra tür önerisi listesi
            parcalar.append(f'  <ul class="ok-liste">{oneri_ln}</ul>')
    h2_bloklari = "".join(parcalar)
    h3_blok = ilce_h3_blok(i)
    tur_bolumu = ilce_tur_bolumu(i)

    return head(baslik, aciklama, yol, sema) + ust_header() + f"""
{kirinti([("Ana Sayfa", "/"), ("İlçeler", "/ilceler/"), (ad, None)])}
<main id="ana">
<section class="hero hero-ic">
  <div class="kap">
    {hero_h1([f"{ad} İskele Kiralama", S["tel"]])}
    <p class="hero-alt">{e(ad)} ve çevresinde cephe iskelesi kurulumu, aylık kiralama ve söküm.
       {e(merkez_cumlesi(i))}</p>
    <div class="dg-grup">{tel_btn()}{wa_btn(f"Merhaba, {ad} için iskele kiralamak istiyorum.")}</div>
  </div>
</section>

{guven_seridi()}

<section class="bol"><div class="kap">{vitrin(ilce_gorseli(i), oncelik=True)}</div></section>

<section class="bol"><div class="kap dar metin">{h2_bloklari}
{h3_blok}
{tur_bolumu}
  <p>{ana_link_c}</p>
</div></section>

{sss_bolum(sorular, f"{ad} İskele Kiralama — Sık Sorulan Sorular")}

{harita_bolum(i)}

<section class="bol komsu"><div class="kap">
  <h2>Yakın İlçeler</h2>
  <p class="giris">{e(ad)}'a komşu ilçelerde de aynı ekip çalışıyor:</p>
  <ul class="ilce-liste">{komsu_ln}</ul>
</div></section>

{cta_band(f"{ek(i)} iskele mi gerekiyor?",
          "Cephe enini ve kat sayısını söyleyin, aralık verelim; ölçüyü yerinde alıp net fiyatı çıkaralım.")}
</main>
{alt_bilgi()}"""


# ── İlçe sayfasındaki tür bölümü + örümcek ağı ──────────────────────────────
# Kullanıcı 2026-09-01'de 39×15 = 585 ayrı sayfa istedi; risk tablosu sunuldu
# (ölçeklendirilmiş içerik + 585 kopya metin) ve **bu yapı seçildi**: türler ilçe
# sayfasının içinde H3 bölümleri olarak duruyor, çapraz linkler ilçe+tür anchor'ıyla
# veriliyor. ⛔ Tekrar 585 sayfaya çıkarma isteği gelirse bu kararı hatırlat.

def tur_tanitim(t, i, uzun):
    """Bir türün ilçe sayfasındaki tanıtımı. uzun=True → kullanıcının örnek metni
    tarzında tam tanıtım; False → iki cümle + link."""
    ad, yer = t["ad"], ek(i)
    if not uzun:
        return (f'<p>{e(t["ozet"])} '
                f'<a href="/{t["slug"]}/">{e(t["ad"])} sayfasında</a> ayrıntısını yazdım.</p>')
    return (
        f'<p>{e(yer)} {e(kucuk(ad))} kiralama fiyatlarını merak ediyorsanız doğru yerdesiniz :) '
        f'{e(t["ozet"])}</p>'
        f'<p>Bir telefon yeterli — projeyi dinleyip ölçüyü alalım, size net teklifimizi sunalım. '
        f'Keşif ücretsiz, çalışma sigortalı; her gün 08:30-19:00 arası açığız. '
        f'{e(t["kimin"])} için uygun. Sınırını da söyleyeyim: {e(kucuk(t["sinir"][:1]) + t["sinir"][1:])}</p>'
        f'<p>Detayını <a href="/{t["slug"]}/">{e(t["ad"])}</a> sayfasında anlattım.</p>')


def ilce_tur_bolumu(i):
    """18 türün tamamı H3 olarak; ilçeye uyanlar tam tanıtım, kalanlar kısa.
    Her bölümün sonunda BAŞKA bir ilçeye 'ilçe + tür' anchor'lı çapraz link var —
    örümcek ağı bu şekilde kuruluyor, ayrı sayfa açmadan."""
    metin = " ".join([i["doku"], i["vurgu"]]).lower()
    # ⚠️ Tam tanıtım + görsel alan tür sayısı 4 ile SINIRLI. Kural serbest bırakılınca
    #    ilçe başına ~14 vitrin çıkıyordu (sayfa 1,5 MB görsel); "dar sokak" gibi
    #    yaygın ifadeler her ilçede birden çok kategoriyi tetikliyor.
    puan = collections.Counter()
    KURAL = [
        (("yüksek", "rezidans", "plaza", "blok", "on iki"),
         ("sistem-iskele", "asma-iskele", "flansli-iskele", "merdivenli-iskele")),
        (("mantolama", "yalıtım", "güçlendirme", "dönüşüm"),
         ("mantolama-iskelesi", "cephe-iskelesi", "h-tipi-iskele")),
        (("depo", "fabrika", "imalathane", "sanayi", "tersane", "liman"),
         ("endustriyel-iskele", "mobil-iskele", "kalip-alti-iskelesi", "cuplock-iskele")),
        (("tarihi", "bitişik", "restorasyon", "koruma"),
         ("konsol-iskele", "mobil-iskele", "asma-iskele")),
        (("villa", "müstakil", "eğim", "yamaç", "bahçe"),
         ("h-tipi-iskele", "kamali-iskele", "boya-badana-iskelesi")),
    ]
    for kelimeler, sluglar in KURAL:
        if any(x in metin for x in kelimeler):
            for n, s in enumerate(sluglar):
                puan[s] += 10 - n
    for s in ("cephe-iskelesi", "h-tipi-iskele"):
        puan[s] += 5                      # her ilçede taban
    secilen = {s for s, _ in puan.most_common(4)}
    def uygun(t):
        return t["slug"] in secilen

    # çapraz link için komşular + graf uzağındaki ilçeler karıştırılıyor
    komsular = [ILCE[k] for k in KOMSU.get(i["slug"], []) if k in ILCE]
    hepsi = [x for x in D.ILCELER if x["slug"] != i["slug"]]
    baslangic = D.ILCELER.index(i)

    parcalar = [f'\n  <h2>{e(ek(i))} Kiraladığımız İskele Çeşitleri</h2>',
                f'<p>Aşağıda {e(ek(i, "gen"))} işlerinde en çok kurduğumuz sistemleri tek tek '
                f'yazdım. Hangisinin sizin işinize oturduğundan emin değilseniz hiç uğraşmayın, '
                f'arayın — keşifte binayı görüp birlikte karar veriyoruz :)</p>']

    for n, t in enumerate(D.TURLER):
        tam = uygun(t)
        parcalar.append(f'  <h3>{e(ek(i))} {e(kucuk(t["ad"]))} kiralama</h3>')
        # ⚠️ Görsel yalnız tam tanıtım alan türlerde: 18 görsel sayfayı boğuyor,
        #    lazy yüklense bile düzen ve kaydırma ağırlaşıyor.
        if tam:
            parcalar.append("  " + vitrin(D.TUR_GORSEL.get(t["slug"]),
                                          yazi=f"{ek(i)} {kucuk(t['ad'])} için ara: {S['tel']}"))
        parcalar.append("  " + tur_tanitim(t, i, tam))
        # çapraz link: başka bir ilçe + başka bir tür — anchor'da ikisi birlikte
        hedef = (komsular[n % len(komsular)] if komsular and n % 2 == 0
                 else hepsi[(baslangic + n * 7) % len(hepsi)])
        capraz_tur = D.TURLER[(n + 5) % len(D.TURLER)]
        parcalar.append(
            f'  <p class="capraz">Yakındaki ilçelerde de aynı ekip çalışıyor: '
            f'<a href="{ilce_yolu(hedef)}">{e(ek(hedef))} {e(kucuk(capraz_tur["ad"]))} '
            f'kiralama</a>.</p>')
    return "\n".join(parcalar)


def tur_ilce_agi(t):
    """Tür sayfasından 39 ilçeye giden ağ. Anchor 'ilçe + tür' biçiminde."""
    ln = "".join(
        f'<li><a href="{ilce_yolu(i)}">{e(ek(i))} {e(kucuk(t["ad"]))} kiralama</a></li>'
        for i in D.ILCELER)
    return (f'<section class="bol ilceler"><div class="kap">'
            f'<h2>{e(t["ad"])} Kiraladığımız İlçeler</h2>'
            f'<p class="giris">İstanbul\'un tüm ilçelerine kurulum yapıyoruz. İlçenize ait '
            f'sayfada o bölgede sık karşılaştığımız zemin, sokak ve yapı stoğu notlarını '
            f'bulabilirsiniz.</p>'
            f'<ul class="ilce-liste">{ln}</ul></div></section>')


# ── İskele türü sayfası ─────────────────────────────────────────────────────
def tur_sss(t):
    return [
        (f"{t['ad']} hangi işler için uygun?", e(t["kimin"]) + "."),
        (f"{t['ad']} için keşif gerekiyor mu?",
         "Gerekiyor. Ölçü, zemin ve erişim görülmeden verilen rakam tahmin olur. Keşifte cepheyi "
         "ölçüp aracın yanaşacağı yeri de belirliyoruz."),
        (f"{t['ad']} ne zaman doğru seçim olmaz?", e(t["sinir"])),
        ("Kurulumu siz mi yapıyorsunuz?",
         "Evet, kurulum ve söküm bize ait. Malzemeyi bırakıp gitmiyoruz; iş bitince toplayıp "
         "götürüyoruz, depolama ve bakım sizin derdiniz olmuyor."),
    ]


# ── Tür sayfası içerik bölümleri ────────────────────────────────────────────
# Kullanıcı 2026-09-01: her tür sayfası kendi konusunda şu sorulara cevap versin —
# "X nedir?", "İstanbul'da nereden kiralanır?", "ne kadara kiralanır?",
# "teslim süreci nasıl?". Tamamı İstanbul odaklı ve kullanıcının kendi diliyle
# ([[feedback_web4medya_kullanici_dili]]): 1. şahıs usta sesi, `:)` ve `..`,
# dürüst uyarılar. ⚠️ Uydurma rakam YOK — fiyat listesi hâlâ onaylanmadı.

def tur_nedir(t):
    teknik = t["teknik"][0] if t["teknik"] else ""
    return (f'<h2>{e(t["ad"])} Nedir?</h2>'
            f'<p>{e(t["ozet"])} Kısaca anlatayım: {e(teknik[0].lower() + teknik[1:])}</p>'
            f'<p>Sahada en çok karıştırılan konu bu oluyor — "iskele iskeledir" deyip '
            f'geçmeyin :) Her sistemin kendi mantığı, kendi kurulum düzeni ve kendi '
            f'sınırı var. Yanlış sistem seçmek hem paradan hem zamandan götürüyor.</p>')

def tur_nereden(t):
    ad = t["ad"]
    # İstanbul odağı: merkez + iki yaka + örnek ilçe bağlantıları
    ornek = [i for i in D.ILCELER if i["slug"] in
             ("esenyurt", "kadikoy", "basaksehir", "umraniye", "bagcilar", "maltepe")]
    ln = " · ".join(f'<a href="{ilce_yolu(i)}">{e(i["ad"])}</a>' for i in ornek)
    return (f'<h2>İstanbul\'da {e(ad)} Nereden Kiralanır?</h2>'
            f'<p>Bizden :) Deha İskele olarak depomuz <strong>{e(S["adres_ilce"])}</strong>\'da; '
            f'ekip Avrupa ve Anadolu yakasının tamamına aynı yerden çıkıyor. Yani '
            f'{e(ad.lower())} için İstanbul\'un neresinde olursanız olun aynı ekiple '
            f'çalışıyorsunuz.</p>'
            f'<p>Bir telefon yeterli: <a href="tel:{S["tel_link"]}">{e(S["tel"])}</a> ya da '
            f'<a href="tel:{S["tel2_link"]}">{e(S["tel2"])}</a>. Her gün 08:30 – 19:00 arası '
            f'açığız, Pazar dahil. Keşif ücretsiz — gelip cepheyi ölçüyor, zemini ve aracın '
            f'yanaşacağı yeri görüyoruz.</p>'
            f'<p>Sık çalıştığımız ilçelerden birkaçı: {ln} — '
            f'<a href="/ilceler/">39 ilçenin tamamına</a> kurulum yapıyoruz.</p>')

def tur_fiyat_bolumu(t):
    return (f'<h2>İstanbul\'da {e(t["ad"])} Kiralama Fiyatları</h2>'
            f'<p>Size dobra söyleyeyim: sabit bir liste fiyatı yok, olamaz da. Rakam dört '
            f'kalemden çıkıyor — <strong>cephe metrekaresi</strong>, <strong>kiralama '
            f'süresi</strong>, <strong>kurulum-söküm işçiliği</strong> ve '
            f'<strong>nakliye</strong>.</p>'
            f'<p>Metrekare hesabı basit: cephe eni × bina yüksekliği. Beş katlı, 12 metre '
            f'enindeki bir cephe kabaca 170-180 m² ediyor.. Kendi ölçünüzü '
            f'<a href="/#hesap">hesaplayıcıdan</a> çıkarıp arayabilirsiniz, telefonda '
            f'aralık veririm. Kesin rakam keşiften sonra çıkıyor çünkü balkon, çıkma, '
            f'saçak ve zemin kotu ölçüyü değiştiriyor.</p>'
            f'<p>Kiralama süresi de işinize göre: <strong>günlük, haftalık ve aylık</strong> '
            f'seçeneklerimiz var. Kısa işlerde günlük, uzun soluklu projelerde aylık en '
            f'ekonomiği oluyor. Neyin fiyatı ne kadar değiştirdiğini '
            f'<a href="/iskele-kiralama-fiyatlari/">fiyat rehberinde</a> kalem kalem yazdım.</p>'
            f'<p><strong>Bir uyarı:</strong> ölçü almadan telefonda kesin rakam veren birine '
            f'temkinli yaklaşın. O rakam keşiften sonra değişir.</p>')

def tur_teslim(t):
    return (f'<h2>Teslim ve Kurulum Süreci Nasıl İşliyor?</h2>'
            f'<ol class="adim">'
            f'<li><strong>Arayın, kabaca anlatın.</strong> Kat sayısı ve cephe eni yeterli; '
            f'telefonda aralık verelim.</li>'
            f'<li><strong>Ücretsiz keşif.</strong> Geliyoruz; cepheyi ölçüyor, zemini ve '
            f'aracın yanaşacağı yeri görüyoruz.</li>'
            f'<li><strong>Net fiyat ve tarih.</strong> Metrekare, süre ve işçilik netleşince '
            f'rakamı ve kurulum gününü söylüyoruz. Sonradan kalem eklenmiyor.</li>'
            f'<li><strong>Teslimat ve kurulum.</strong> Malzeme sahaya geliyor, zemin '
            f'hazırlanıyor, {e(kucuk(t["ad"]))} kuruluyor. Normal bir apartman cephesinde '
            f'iş çoğunlukla bir günde bitiyor.</li>'
            f'<li><strong>Teslim kontrolü.</strong> Korkuluk, platform, topuk levhası ve '
            f'bağlantılar tek tek gözden geçiriliyor. İskele ondan sonra sizin.</li>'
            f'<li><strong>Söküm.</strong> İş bitince bir telefon yeterli; sökümü biz '
            f'yapıyoruz, malzeme sizde kalmıyor.</li>'
            f'</ol>'
            f'<p>Tüm süreci adım adım <a href="/iskele-kurulum-sokum-sureci/">kurulum ve '
            f'söküm rehberinde</a> anlattım.</p>')

def tur_sayfasi(t):
    yol = f'/{t["slug"]}/'
    sorular = tur_sss(t)
    # Kullanıcı 2026-09-01: tüm tür sayfalarında H1 ve <title> aynı kalıpta olacak —
    # "İstanbul {Tür} Kiralama - Deha İskele". SERP başlığı ile H1 birebir aynı.
    h1 = f"İstanbul {t['ad']} Kiralama - {S['marka']}"
    baslik = h1
    if len(baslik) > 70:
        baslik = f"İstanbul {t['ad']} Kiralama | {S['marka']}"
    aciklama = f"{t['ozet']} İstanbul genelinde kurulum ve söküm dahil. {S['tel']}"
    sema = (isletme_semasi() + sss_semasi(sorular) +
            ldj({"@context": "https://schema.org", "@type": "Service",
                 "serviceType": t["ad"], "name": t["h1"],
                 "provider": {"@id": ALAN + "/#isletme"},
                 "areaServed": {"@type": "City", "name": "İstanbul"},
                 "url": ALAN + yol}))
    teknik_ln = "".join(f"<li>{e(x)}</li>" for x in t["teknik"])
    return head(baslik, aciklama, yol, sema) + ust_header() + f"""
{kirinti([("Ana Sayfa", "/"), ("İskele Çeşitleri", "/iskele-cesitleri/"), (t["ad"], None)])}
<main id="ana">
<section class="hero hero-ic">
  <div class="kap">
    {hero_h1([h1])}
    <p class="hero-slogan">{e(t["h1"])}</p>
    <p class="hero-alt">{e(t["ozet"])}</p>
    <div class="dg-grup">{tel_btn()}{wa_btn(f"Merhaba, {t['ad']} hakkında bilgi almak istiyorum.")}</div>
  </div>
</section>

{guven_seridi()}

<section class="bol"><div class="kap">{vitrin(D.TUR_GORSEL.get(t["slug"]), oncelik=True)}</div></section>

<section class="bol"><div class="kap dar metin">
  {tur_nedir(t)}

  <h2>İstanbul'da {e(t["ad"])} Kimler İçin Uygun?</h2>
  <p>{e(t["kimin"])}.</p>

  {tur_nereden(t)}

  {tur_fiyat_bolumu(t)}

  {tur_teslim(t)}

  <h2>Kurulumda Neye Dikkat Ediyoruz?</h2>
  <ul class="ok-liste">{teknik_ln}</ul>

  <h2>Sınırı Nerede?</h2>
  <p>{e(t["sinir"])}</p>
  <p>Bunu size baştan söylemeyi tercih ediyorum :) Her işe her sistemi satmak kolay ama yanlış
     tür seçmek hem cebinizden hem zamanınızdan gidiyor. Keşifte binayı görünce hangisinin
     oturduğunu birlikte belirliyoruz.</p>

  <h2>İş Güvenliği</h2>
  <p>Burada pazarlık yok. Korkuluk, platform genişliği ve bağlantı düzeni tercih meselesi değil,
     mevzuatın koyduğu asgari şartlar. Hangi yönetmeliğin ne dediğini
     <a href="/iskele-is-guvenligi/">iş güvenliği sayfasında</a> Resmî Gazete tarih ve
     sayısıyla birlikte yazdım — merak ederseniz kaynağından okuyabilirsiniz.</p>
</div></section>

{sss_bolum(sorular)}
{tur_ilce_agi(t)}
{tur_kartlari("Diğer İskele Sistemleri", haric=t["slug"])}
{cta_band("Hangi iskele sizin işinize uyar?",
          "İşi ve binayı anlatın, uygun sistemi birlikte seçelim. Keşif için ölçüyü yerinde alıyoruz.")}
</main>
{alt_bilgi()}"""

# ── Anasayfa ────────────────────────────────────────────────────────────────
ANA_SSS = [
    ("İskele kiralama fiyatı nasıl hesaplanıyor?",
     "Dört kalemden çıkıyor: cephe metrekaresi (cephe eni × bina yüksekliği), iskelenin kaç ay "
     "duracağı, kurulum-söküm işçiliği ve nakliye. Kat sayısı ile cephe enini söylerseniz "
     "telefonda size bir aralık verebilirim. Ama dobra söyleyeyim: ölçü almadan kesin rakam "
     "veren birine temkinli yaklaşın, o rakam keşiften sonra değişir."),
    ("İskeleyi siz mi kuruyorsunuz?",
     "Evet, kurulum da söküm de bize ait. Malzemeyi kapınıza bırakıp gitmiyoruz; iş bitince "
     "toplayıp götürüyoruz. Depolama, taşıma ve bakım sizin derdiniz olmuyor."),
    ("İstanbul'un hangi ilçelerine geliyorsunuz?",
     "Avrupa ve Anadolu yakasının tamamına. Depomuz Eyüpsultan'da, ekip iki yakaya da aynı "
     "yerden çıkıyor. İlçenize ait sayfada o bölgede sık karşılaştığımız durumları yazdım — "
     "zemin, sokak genişliği, yapı stoğu gibi."),
    ("İskele en az ne kadar süreyle kiralanıyor?",
     "Üç seçenek var: günlük, haftalık ve aylık. Kısa süreli ve acil işlerde günlük, orta vadeli "
     "işlerde haftalık, uzun soluklu projelerde aylık kiralama en ekonomiği oluyor. Tavsiyem "
     "süreyi olduğundan kısa söylememeniz.. \"İki haftada biter\" deyip iki ay süren çok iş "
     "gördüm. Süre uzarsa yeni bir kurulum ücreti çıkmıyor, kiralama devam ediyor."),
    ("Keşif için ücret alıyor musunuz?",
     "Keşifte cepheyi ölçüyor, zemini ve aracın yanaşacağı yeri görüyoruz. Ölçü almadan verilen "
     "rakam tahminden ibaret; o yüzden önce yerinde bakmayı tercih ediyorum."),
    ("Kurulum ne kadar sürüyor?",
     "Normal bir apartman cephesinde çoğunlukla bir gün. Yüksek blokta, dar sokakta ve eğimli "
     "zeminde uzuyor. Kurulum gününü baştan söylüyoruz ki bina da kendi işini ona göre "
     "planlasın — komşulara haber vermek bile zaman istiyor :)"),
]

def anasayfa():
    yol = "/"
    # Google sonuçlarında çıkacak başlık (kullanıcı 2026-09-01'de bu biçimi istedi).
    # H1 ile birebir aynı tutuldu ki SERP ile sayfa arasında kopukluk olmasın.
    baslik = "İstanbul İskele Kiralama - Deha İskele"
    aciklama = ("İstanbul'un tüm ilçelerinde cephe iskelesi kiralama, kurulum ve söküm. "
                "Keşifle net ölçü, aylık kira. Eyüpsultan merkezli ekip: " + S["tel"])
    sema = (isletme_semasi() + sss_semasi(ANA_SSS) +
            ldj({"@context": "https://schema.org", "@type": "WebSite",
                 "name": S["marka"], "url": ALAN + "/",
                 "inLanguage": "tr-TR"}))
    return head(baslik, aciklama, yol, sema) + ust_header(aktif="/") + f"""
<main id="ana">
<section class="hero hero-ana hero-tam">
  <div class="hero-fon">{gorsel(D.HERO_GORSEL, D.GORSEL_ALT[D.HERO_GORSEL], boy="100vw", oncelik=True)}</div>
  <div class="kap hero-metin">
    <p class="hero-ust">İstanbul İskele Kiralama Firması</p>
    {hero_h1(["İstanbul İskele Kiralama - Deha İskele"])}
    <p class="hero-slogan">“Güvenli Yapılar, Sağlam İskeleler.”</p>
    <p class="hero-alt">Cephenizi gelip ölçüyoruz, metrekare üzerinden net konuşuyoruz.
       Kurulum da söküm de bize ait — siz sadece işinizi yapıyorsunuz.</p>
    <div class="dg-grup">{tel_btn()}{teklif_btn("dg dg-cerceve")}</div>
    <ul class="hero-cip">
      <li>10+ yıl deneyim</li><li>39 ilçe</li><li>18 iskele sistemi</li>
      <li>Her gün 08:30 – 19:00</li>
    </ul>
  </div>
</section>

{guven_seridi()}
{tur_kartlari("Hizmetlerimiz", giris="Kiraladığımız 18 iskele sistemini detaylı olarak inceleyin.")}
{bolunmus_bolum()}
{kiralama_donemleri()}
{hesaplayici()}

{seo_icerik()}
{video_bolum()}
{tanitim_bolum()}
{sss_bolum(ANA_SSS)}
{harita_bolum()}
{ilce_agi()}
{cta_band("Cephenizi ölçelim, net konuşalım",
          "Kat sayısını ve cephe enini söyleyin; aralığı telefonda verelim, kesin fiyatı keşifte çıkaralım.")}
</main>
{alt_bilgi()}"""

# ── Rehber sayfaları ────────────────────────────────────────────────────────
# ⚠️ MEVZUAT REFERANSLARI: Yapı İşlerinde İSG Yönetmeliği (RG 05.10.2013 / 28786) ve
#    İş Ekipmanlarının Kullanımında Sağlık ve Güvenlik Şartları Yönetmeliği
#    (RG 25.04.2013 / 28628). Sayısal asgari şartlar (korkuluk 100 cm, topuk levhası
#    15 cm, platform genişliği 60 cm) bu yönetmeliklerin ekleri kaynaklıdır.
#    ⏳ Yayından önce kullanıcı/uzman teyidi alınacak.

def r_fiyat():
    sorular = [
        ("İskele kirası neye göre hesaplanıyor?",
         "Cephe metrekaresi ve süre. Metrekare, cephe eni ile bina yüksekliğinin çarpımı; süre "
         "ise iskelenin kaç ay duracağı. Bu ikisinin üstüne kurulum-söküm işçiliği ve nakliye "
         "biniyor."),
        ("Kurulum ve söküm kira fiyatına dahil mi?",
         "İkisi ayrı kalem olarak konuşuluyor. Kısa süreli işlerde kurulum-söküm toplam maliyette "
         "kiradan büyük yer tutabiliyor; uzun süreli şantiyelerde ise kira öne geçiyor."),
        ("Aynı metrekarede fiyat neden değişiyor?",
         "Erişim ve zemin. Dar sokakta kamyon yanaşamıyorsa malzeme elden taşınıyor, eğimli "
         "zeminde ayak kotları ayrı ayrı ayarlanıyor, yüksek blokta bağlantı sayısı artıyor. "
         "Metrekare aynı olsa da işçilik değişiyor."),
        ("Telefonda fiyat alabilir miyim?",
         "Aralık alabilirsiniz: kat sayısı ve cephe eni yeterli. Kesin rakam keşiften sonra "
         "çıkıyor, çünkü balkon, çıkma, saçak ve zemin kotu ölçüyü değiştiriyor."),
    ]
    govde = """
  <p>Bana en çok sorulan soru bu: "Abi iskele ne kadar?" :) Keşke tek bir rakam söyleyebilsem
     ama öyle çalışmıyor. Fiyat dört kalemin toplamı; bunları ayrı ayrı bilirseniz aldığınız
     teklifleri de düzgün karşılaştırırsınız.</p>

  <h2>1. Cephe metrekaresi</h2>
  <p>İskelenin ölçü birimi metrekare. Hesap basit: <strong>cephe eni × bina yüksekliği</strong>.
     Beş katlı, kat yüksekliği 2,9 metre olan bir binanın yüksekliği yaklaşık 14,5 metre;
     cephe eni 12 metreyse iskele kabaca 174 m² tutuyor.</p>
  <p>Birden fazla cephe kurulacaksa her cephe ayrı hesaplanıp toplanıyor. Kendi ölçünüzü
     <a href="/#hesap">cephe metrekaresi hesaplayıcısından</a> çıkarabilirsiniz.</p>

  <h2>2. Süre</h2>
  <p>Kiralama süresi üç şekilde işliyor: <strong>günlük</strong>, <strong>haftalık</strong> ve
     <strong>aylık</strong>. Kısa süreli ve acil işlerde günlük, orta vadeli işlerde haftalık,
     uzun soluklu projelerde aylık kiralama en ekonomiği oluyor.</p>
  <p>Dış cephe boyası çoğu zaman birkaç haftada bitiyor; mantolama, sıva yenileme ve
     güçlendirme işleri aylara yayılıyor. Süreyi olduğundan kısa söylemek sonradan hesabı
     şaşırtıyor — işin gerçek takvimini baştan konuşmak hem size hem bize daha sağlıklı.
     Hangi dönemin sizin işinize oturduğunu telefonda birlikte belirleyebiliriz.</p>

  <h2>3. Kurulum ve söküm işçiliği</h2>
  <p>Bu kalem metrekareyle doğru orantılı değil; işin zorluğuyla orantılı. Dar sokak, eğimli
     zemin, yüksek blok ve yaya trafiği kurulum süresini uzatıyor. Kısa süreli işlerde bu kalem
     kiradan büyük çıkabiliyor, bu yüzden "aylık ne kadar?" sorusu tek başına yeterli olmuyor.</p>

  <h2>4. Nakliye</h2>
  <p>Malzemenin depodan sahaya gidip gelmesi. Mesafe ve aracın yanaşabildiği nokta belirleyici;
     kamyon sokağa giremiyorsa malzeme elden taşınıyor ve bu süre işçiliğe yansıyor.</p>

  <h2>Teklifleri karşılaştırırken</h2>
  <ul class="ok-liste">
    <li>Rakamın <strong>hangi metrekare</strong> için verildiğini sorun — cephe ölçüsü mü,
        iskelenin kaplayacağı alan mı?</li>
    <li><strong>Kurulum-söküm dahil mi</strong>, ayrı mı?</li>
    <li>Kira <strong>hangi süre</strong> için? Uzarsa nasıl işleyecek?</li>
    <li><strong>Nakliye</strong> ve varsa <strong>koruma filesi</strong> fiyata dahil mi?</li>
    <li>Söküm sonrası <strong>alan temizliği</strong> kimde?</li>
  </ul>
  <p>Son olarak size dobra bir şey söyleyeyim: ölçü almadan telefonda net rakam veren teklif,
     çoğu zaman keşiften sonra değişiyor.. Aralık vermek başka, kesin fiyat vermek başka.
     Ben telefonda aralık veriyorum, kesin rakamı cepheyi ölçtükten sonra söylüyorum — ikisini
     karıştırmayalım.</p>
"""
    return govde, sorular

def r_guvenlik():
    sorular = [
        ("İskelede korkuluk zorunlu mu?",
         "Evet. Yapı İşlerinde İş Sağlığı ve Güvenliği Yönetmeliği (RG 05.10.2013 / 28786) "
         "düşme riski bulunan çalışma yerlerinde korkuluk sistemi arıyor: ana korkuluk, ara "
         "korkuluk ve malzeme düşmesini önleyen topuk levhası birlikte."),
        ("İskeleyi herkes kurabilir mi?",
         "Hayır. Mevzuat iskelelerin kurulması, sökülmesi ve önemli değişikliklerinin ehil "
         "kişilerin gözetiminde, konuyla ilgili eğitim almış çalışanlarca yapılmasını istiyor."),
        ("İskele kurulduktan sonra kontrol gerekiyor mu?",
         "Gerekiyor. Kurulum sonrası teslim kontrolü yapılıyor; ayrıca kullanım süresince, "
         "özellikle fırtına gibi olaylardan sonra ve iskelede değişiklik yapıldığında yeniden "
         "kontrol edilmesi gerekiyor."),
        ("İskeleye kendim ekleme yapabilir miyim?",
         "Yapmayın. Korkuluğun sökülmesi, platformun kaydırılması veya bağlantının çıkarılması "
         "iskelenin taşıma ve devrilme davranışını değiştiriyor. Bir şeyin yerinden oynaması "
         "gerekiyorsa bize haber verin, biz düzenleyelim."),
    ]
    govde = """
  <p>Bu sayfayı biraz da içim rahat etsin diye yazdım. İskele, üzerinde insan çalışan geçici
     bir yapı; "olsa da olur" denecek hiçbir parçası yok. Aşağıdakiler benim tercihim değil,
     mevzuatın aradığı asgari şartlar — kaynaklarını da veriyorum ki isteyen kendisi baksın.</p>

  <h2>Hangi mevzuat?</h2>
  <p>İki temel düzenleme var:</p>
  <ul class="ok-liste">
    <li><strong>Yapı İşlerinde İş Sağlığı ve Güvenliği Yönetmeliği</strong> — Resmî Gazete
        5 Ekim 2013, sayı 28786. Yapı alanındaki çalışma yerlerinin asgari şartlarını,
        düşmeye karşı korunmayı ve iskelelere ilişkin hükümleri içeriyor.</li>
    <li><strong>İş Ekipmanlarının Kullanımında Sağlık ve Güvenlik Şartları Yönetmeliği</strong> —
        Resmî Gazete 25 Nisan 2013, sayı 28628. Yüksekte çalışmada kullanılan ekipmanın
        seçimi, kurulumu ve kontrolüne ilişkin şartları düzenliyor.</li>
  </ul>
  <p>Her ikisinin dayanağı 6331 sayılı İş Sağlığı ve Güvenliği Kanunu.</p>

  <h2>Korkuluk sistemi</h2>
  <p>Düşme riski olan her çalışma platformunda korkuluk şart. Üç parçası birlikte aranıyor:</p>
  <ul class="ok-liste">
    <li><strong>Ana korkuluk</strong> — platform seviyesinden en az 100 cm yükseklikte.</li>
    <li><strong>Ara korkuluk</strong> — açıklığı bölerek gövdenin geçmesini engelliyor.</li>
    <li><strong>Topuk levhası (etek tahtası)</strong> — en az 15 cm; aşağıya malzeme düşmesini
        önlüyor. Altında insan geçiyorsa bu parça hayati.</li>
  </ul>

  <h2>Çalışma platformu</h2>
  <p>Platform genişliği çalışanın güvenle durabileceği ölçüde olmalı; mevzuat asgari 60 cm
     genişlik arıyor. Platformda boşluk bırakılmaması, elemanların kaymaya karşı sabitlenmesi
     ve üzerinde biriken malzemenin geçişi kapatmaması gerekiyor.</p>

  <h2>Kurulum, söküm ve ehil kişi</h2>
  <p>İskelenin kurulması, sökülmesi veya önemli ölçüde değiştirilmesi ehil kişi gözetiminde,
     bu konuda eğitim almış çalışanlar tarafından yapılıyor. Kurulum planı; iskelenin tipi,
     taşıma sınıfı, bağlantı düzeni ve zemin şartlarına göre belirleniyor.</p>

  <h2>Zemin ve bağlantı</h2>
  <p>İskele ancak oturduğu zemin kadar sağlam. Taban plakalarının yükü dağıtacak biçimde
     oturması, yumuşak zeminde altlık kullanılması ve kot farkının ayarlı ayakla düzeltilmesi
     gerekiyor. Cepheye yapılan bağlantılar ise devrilmeye karşı asıl güvenlik; koruma filesi
     gerildiğinde rüzgâr yükü arttığı için bağlantı sıklığı da artıyor.</p>

  <h2>Kontrol ve kayıt</h2>
  <p>Kurulum bittiğinde teslim kontrolü yapılıyor. Kullanım süresince iskelenin durumunun
     izlenmesi; fırtına, çarpma veya iskelede değişiklik gibi durumlardan sonra yeniden
     kontrol edilmesi gerekiyor. Uzun süreli şantiyelerde kontrolün kayda geçmesi, kimin ne
     zaman doğruladığının belli olması açısından önemli.</p>

  <h2>Size Üç Ricam Var</h2>
  <ol class="adim">
    <li><strong>Korkuluğu sökmeyin.</strong> Sahada en sık gördüğüm şey bu: "malzeme geçmiyor"
        diye çıkarılan korkuluk. Lütfen yapmayın.. Malzeme geçmiyorsa bize söyleyin, biz
        geçirecek düzeni kurarız.</li>
    <li><strong>Platformu depo yapmayın.</strong> Platformun yük sınırı var ve üstünde biriken
        malzeme geçişi kapatıyor. Aynı anda hem malzeme hem insan olduğunda iş zorlaşıyor.</li>
    <li><strong>Bir şey oynadıysa arayın.</strong> Fırtınadan sonra, bir yere çarptıktan sonra
        ya da bir parça gevşediğinde haber verin. Geliyoruz, bakıyoruz, düzeltiyoruz — bunun
        için ayrıca bir şey istemiyoruz, işin parçası :)</li>
  </ol>
"""
    return govde, sorular

def r_surec():
    sorular = [
        ("Keşif ne kadar sürüyor?",
         "Çoğu apartmanda yarım saatlik bir iş. Cepheyi ölçüyor, zemini ve aracın yanaşacağı "
         "yeri görüyoruz."),
        ("Kurulum günü binada olmam gerekiyor mu?",
         "Şart değil ama birinin ulaşılabilir olması iyi oluyor; özellikle site yönetimi izni, "
         "otopark kullanımı ve bahçe kapısı gibi konularda."),
        ("Söküm için ayrıca ücret ödüyor muyum?",
         "Söküm işçiliği baştan konuşulan kalemlerin içinde yer alıyor; iş bitiminde sürpriz "
         "bir kalem çıkmıyor."),
        ("İskele kaldıktan sonra cephede iz kalır mı?",
         "Cepheye yapılan bağlantı noktaları küçük delikler bırakıyor. Mantolama ve boya "
         "işlerinde bu noktalar zaten uygulamanın içinde kapanıyor; diğer işlerde nasıl "
         "kapatılacağını baştan konuşuyoruz."),
    ]
    govde = """
  <p>İskele işi bir telefonla başlıyor, sökümle bitiyor. Arada altı adım var. Hepsini yazayım
     ki siz de kendi işinizi buna göre planlayın — özellikle bina yönetimiyle konuşacaksanız
     bu takvim işinize yarar :)</p>

  <h2>1. Telefon</h2>
  <p>Kat sayısı ve cephe eni yeterli. Bu ikisiyle kabaca bir aralık verilebiliyor. Binanın
     sokağı dar mı, zemin toprak mı, balkon çıkması var mı — bunları da söylerseniz keşif
     daha hızlı ilerliyor.</p>

  <h2>2. Keşif</h2>
  <p>Yerinde üç şeye bakılıyor: <strong>cephenin gerçek ölçüsü</strong>,
     <strong>iskelenin oturacağı zemin</strong> ve <strong>malzemeyi indirecek aracın
     yanaşacağı yer</strong>. Balkon, çıkma, saçak ve zemin kotu farkı burada ortaya çıkıyor;
     telefondaki aralık bu aşamada net rakama dönüşüyor.</p>

  <h2>3. Fiyat ve tarih</h2>
  <p>Metrekare, süre, işçilik ve nakliye netleşince fiyat ve kurulum günü belli oluyor.
     Site içi işlerde yönetim izni ve çalışma saati kısıtı da bu aşamada konuşuluyor.</p>

  <h2>4. Kurulum</h2>
  <p>Ekip sabah geliyor. Önce zemin hazırlanıyor: yumuşak zeminde altlık atılıyor, eğimde
     ayarlı ayakla kot düzeltiliyor, taban plakaları terazisine oturtuluyor. Sonra iskele kat
     kat yükseliyor; her katta cepheye bağlantılar yapılmadan bir üste çıkılmıyor. Zemin katta
     yaya geçişi varsa koruyucu tünel kuruluyor.</p>
  <p>Normal bir apartman cephesinde kurulum çoğunlukla bir gün sürüyor. Yüksek bloklarda,
     dar sokaklarda ve eğimli arazide bu süre uzayabiliyor.</p>

  <h2>5. Teslim kontrolü</h2>
  <p>Kurulum bitince korkuluklar, platformlar, topuk levhaları ve cephe bağlantıları tek tek
     kontrol ediliyor. İskele bu kontrolden sonra teslim ediliyor. Kullanım süresince
     iskelede değişiklik yapılmaması gerekiyor — korkuluk sökülmüşse veya platform
     kaydırılmışsa haber verin, biz düzeltelim.</p>

  <h2>6. Söküm</h2>
  <p>İş bitince haber vermeniz yeterli. Söküm kurulumun tersi sırayla, yukarıdan aşağıya
     yapılıyor; malzeme toplanıp götürülüyor, alan temizleniyor. Depolama ve bakım yükü
     sizde kalmıyor — kiralamanın satın almaya göre en görünür avantajı bu.</p>
"""
    return govde, sorular

def r_kirala_satin():
    sorular = [
        ("Tek seferlik bir iş için satın almak mantıklı mı?",
         "Genellikle değil. Tek bir cephe boyası için alınan iskele, iş bittikten sonra "
         "depolanacak, taşınacak ve bakılacak bir yük hâline geliyor."),
        ("Hangi noktada satın alma anlam kazanıyor?",
         "Düzenli şantiyesi olan, iskeleyi yıl boyunca farklı işlerde kullanacak firmalarda. "
         "Orada da depolama alanı, taşıma aracı, bakım ve kurulum ekibi hesaba katılmalı."),
        ("Kiralamada malzeme bakımı kimde?",
         "Bizde. Kurulum, söküm, taşıma ve malzemenin bakımı bize ait; siz sadece işin süresi "
         "kadar ödüyorsunuz."),
    ]
    govde = """
  <p>Soru genelde şöyle geliyor: "Kiralamak yerine alsak daha mı iyi olur?" Ben iskele
     kiralayan biriyim ama size dürüst cevap vereyim :) Bazı durumlarda satın almak gerçekten
     daha mantıklı. Cevap işin sıklığına bağlı; rakamlardan önce şu dört yükü hesaba katın.</p>

  <h2>Satın almanın görünmeyen kalemleri</h2>
  <ul class="ok-liste">
    <li><strong>Depolama.</strong> İskele hacimli bir malzeme; iş yokken duracağı kapalı ve
        kuru bir alan gerekiyor.</li>
    <li><strong>Taşıma.</strong> Her işte sahaya götürüp getirmek araç ve işçilik demek.</li>
    <li><strong>Bakım.</strong> Boru, çerçeve ve bağlantı elemanları eğiliyor, paslanıyor,
        kayboluyor. Hasarlı parçayla kurulan iskele risk üretiyor.</li>
    <li><strong>Kurulum bilgisi.</strong> Malzemeye sahip olmak, kurmayı bilmek anlamına
        gelmiyor. Kurulum ve söküm eğitimli ekip işi.</li>
  </ul>

  <h2>Kiralama ne zaman doğru?</h2>
  <p>Tek seferlik ya da yılda birkaç kez tekrarlayan işlerde: apartman dış cephe boyası,
     mantolama, çatı onarımı, tabela ve cephe temizliği. Bu işlerde iskele işin süresi kadar
     duruyor, sonra gidiyor. Ödediğiniz şey malzeme değil, o sürede güvenle çalışabilmek.</p>

  <h2>Satın alma ne zaman doğru?</h2>
  <p>Sürekli şantiyesi olan yapı firmalarında. Orada iskele yılın büyük bölümünde kurulu
     duruyor ve kira toplamı satın alma bedelini geçiyor. Bu durumda bile depolama, taşıma,
     bakım ve ekip maliyetini hesaba katmak gerekiyor; çoğu firma karma çözüme gidiyor —
     temel malzeme kendinde, yoğunlukta ek malzeme kiralık.</p>

  <h2>Aradaki Üçüncü Yol</h2>
  <p>Uzun süreli şantiyelerde iskele aylarca duruyor ve kira toplamı büyüyor. Böyle işlerde
     süreyi baştan konuşup uzun dönem şartlarını netleştirmek, ay ay gitmekten daha mantıklı.
     İşin gerçek takvimini bilmek doğru kararın yarısı.. Siz bana işin ne kadar süreceğini
     dürüstçe söyleyin, ben de size ona göre konuşayım.</p>
"""
    return govde, sorular

def r_cesitler():
    sorular = [
        ("En yaygın iskele türü hangisi?",
         "Cephe iskelesi. Apartman ve site cephelerinde boya, mantolama ve sıva işlerinin "
         "büyük bölümü bu sistemle yapılıyor."),
        ("İç mekân için hangi iskele kullanılıyor?",
         "Kule (seyyar) iskele. Tekerlekli olduğu için nokta işlerde hızlı; yüksek tavanlı "
         "depo ve fabrikalarda da kullanılıyor."),
        ("Yüksek binada cephe iskelesi kurulmuyor mu?",
         "Kurulabiliyor ama belirli bir yükseklikten sonra hem maliyet hem süre büyüyor. "
         "Orada sistem iskele ya da çatıdan askıya alınan platform daha mantıklı oluyor."),
    ]
    kart = "".join(
        f'<tr><td><a href="/{t["slug"]}/"><strong>{e(t["ad"])}</strong></a></td>'
        f'<td>{e(t["kimin"])}</td><td>{e(t["sinir"])}</td></tr>' for t in D.TURLER)
    govde = f"""
  <p>İskele denince çoğu kişinin aklına tek bir şey geliyor: binanın önüne kurulan borulu
     yapı. Oysa sahada birbirinden ayrı sistemler var ve yanlış tür seçmek hem para hem zaman
     kaybı. Aşağıdaki tabloyu tam da bunun için hazırladım — hangisi hangi işe oturuyor,
     yan yana görün.</p>

  <h2>Karşılaştırma Tablosu</h2>
  <div class="tablo-sar">
  <table class="tablo">
    <thead><tr><th>Sistem</th><th>Hangi işler için</th><th>Sınırı</th></tr></thead>
    <tbody>{kart}</tbody>
  </table>
  </div>

  <h2>Seçerken bakılan dört şey</h2>
  <ul class="ok-liste">
    <li><strong>Yükseklik.</strong> Alçak cephede çerçeve iskele yeterli; yükseldikçe sistem
        iskele ve askılı platform öne çıkıyor.</li>
    <li><strong>Cephe geometrisi.</strong> Düz cephe çerçeve iskeleye uygun; çıkma, kademe ve
        düzensiz hatlarda modüler sistem gerekiyor.</li>
    <li><strong>Süre.</strong> Kısa işlerde kurulum-söküm hızı, uzun işlerde aylık kira
        belirleyici oluyor.</li>
    <li><strong>Yük.</strong> Platformda malzeme duracaksa taşıma sınıfı buna göre seçiliyor.</li>
  </ul>
  <p>Kendi işinize hangisinin uyduğundan emin değilseniz hiç uğraşmayın, arayın :) Keşifte
     binayı görüp birlikte karar veriyoruz. Binayı görmeden telefonda sistem önermek bana
     doğru gelmiyor — çünkü çoğu zaman sokak ve zemin, binanın kendisinden daha belirleyici
     oluyor.</p>
"""
    return govde, sorular

REHBER_ICERIK = {
    "iskele-kiralama-fiyatlari": r_fiyat,
    "iskele-is-guvenligi": r_guvenlik,
    "iskele-kurulum-sokum-sureci": r_surec,
    "iskele-kiralama-mi-satin-alma-mi": r_kirala_satin,
    "iskele-cesitleri": r_cesitler,
}

def rehber_sayfasi(r):
    yol = f'/{r["slug"]}/'
    govde, sorular = REHBER_ICERIK[r["slug"]]()
    baslik = f"{r['h1']} | {S['marka']}"
    aciklama = r["ozet"]
    sema = (isletme_semasi() + sss_semasi(sorular) +
            ldj({"@context": "https://schema.org", "@type": "Article",
                 "headline": r["h1"], "description": kirp(r["ozet"]),
                 "inLanguage": "tr-TR", "url": ALAN + yol,
                 "publisher": {"@id": ALAN + "/#isletme"},
                 "mainEntityOfPage": ALAN + yol}))
    ek = tur_kartlari("İskele Sistemleri") if r["slug"] == "iskele-cesitleri" else ""
    return head(baslik, aciklama, yol, sema) + ust_header(aktif=yol) + f"""
{kirinti([("Ana Sayfa", "/"), ("Rehberler", "/iskele-cesitleri/"), (r["ad"], None)])}
<main id="ana">
<section class="hero hero-ic">
  <div class="kap">
    {hero_h1([r["h1"]])}
    <p class="hero-alt">{e(r["ozet"])}</p>
    <div class="dg-grup">{tel_btn()}{wa_btn()}</div>
  </div>
</section>

<section class="bol"><div class="kap">{vitrin(D.GENEL_HAVUZ[D.REHBERLER.index(r) % len(D.GENEL_HAVUZ)], oncelik=True)}</div></section>

<section class="bol"><div class="kap dar metin">{govde}</div></section>

{sss_bolum(sorular)}
{ek}
{cta_band("Kendi cepheniz için ne gerekiyor?",
          "Kat sayısını ve cephe enini söyleyin; aralığı telefonda verelim, kesin fiyatı keşifte çıkaralım.")}
</main>
{alt_bilgi()}"""


# ── Firma tanıtım PDF'i ─────────────────────────────────────────────────────
# ⚠️ PDF DOM'a ancak tıklanınca giriyor (harita ile aynı facade deseni).
#    2,6 MB'lık dosyayı ilk yükte indirmek sayfa hızını — yani gerçek bir sıralama
#    sinyalini — bozardı. Gömülü PDF'in kendisi SEO'ya değer AKTARMAZ; asıl değer
#    aynı içeriğin HTML hâli olan /hakkimizda/ sayfasında.
#    Ayrıca iOS Safari gömülü PDF'i düzgün göstermediği için "yeni sekmede aç"
#    bağlantısı her zaman görünür duruyor.
def tanitim_bolum(baslik="Firma Tanıtımımız"):
    kapak = gorsel("deha-iskele-tanitim-kapak",
                   "Deha İskele firma tanıtım dosyasının kapak sayfası",
                   boy="(min-width:1000px) 620px, 100vw")
    return f"""<section class="bol tanitim" id="tanitim"><div class="kap">
  <h2>{e(baslik)}</h2>
  <p class="giris">Firmamızı, iskele türlerimizi ve hizmet kapsamımızı anlattığımız tanıtım
     dosyamız. Aşağıdan sayfa sayfa inceleyebilir, dilerseniz indirebilirsiniz.</p>
  <div class="tanitim-kutu">
    <div class="pdf-kutu" data-pdf="{e(D.TANITIM_PDF)}">
      <button type="button" class="pdf-ac">{kapak}
        <span class="pdf-rozet">Tanıtımı aç <small>PDF · {e(D.TANITIM_PDF_BOYUT)}</small></span>
      </button>
    </div>
    <div class="tanitim-yan">
      <ul class="ok-liste">
        <li><strong>10 yılı aşkın</strong> saha deneyimi</li>
        <li>18 farklı iskele sistemi, tek firmadan</li>
        <li>Kurulum, söküm ve teknik destek dahil</li>
        <li>Günlük, haftalık ve aylık kiralama</li>
      </ul>
      <div class="dg-grup">
        <a class="dg dg-sari" href="/hakkimizda/">Hakkımızda sayfası</a>
        <a class="dg dg-hat2" href="{e(D.TANITIM_PDF)}" target="_blank" rel="noopener">
          <span>PDF'i yeni sekmede aç</span></a>
      </div>
    </div>
  </div>
</div></section>"""


# ── Hakkımızda sayfası ──────────────────────────────────────────────────────
# Tanıtım PDF'inin HTML karşılığı. ⚠️ Asıl SEO değeri burada: PDF indekslense bile
# gömülü hâli anasayfaya değer aktarmıyor, HTML sayfa aktarıyor.
# Hedef niyet: marka araması ("deha iskele kimdir", "istanbul iskele firması").
HAKKIMIZDA_SSS = [
    ("Deha İskele ne kadar süredir bu işi yapıyor?",
     "10 yılı aşkın süredir İstanbul'da iskele kiralama işindeyiz. Bu sürede apartman "
     "cephesinden fabrika bakımına, tarihi yapı restorasyonundan etkinlik sahnesine kadar "
     "çok farklı iş gördük."),
    ("Hangi iskele sistemlerini kiralıyorsunuz?",
     "18 farklı sistem: cephe, H tipi, flanşlı, kamalı, Cuplock, sistem (modüler), masa, "
     "kalıp altı, mobil, kule, merdivenli, konsol, asma, endüstriyel, mantolama, boya-bakım, "
     "çatı ve sahne iskelesi. Hangisinin işinize oturduğunu keşifte birlikte belirliyoruz."),
    ("Kurulum ve sökümü siz mi yapıyorsunuz?",
     "Evet, ikisi de bize ait. Malzemeyi bırakıp gitmiyoruz; ekibimiz kuruyor, iş bitince "
     "söküp götürüyor. Depolama, taşıma ve bakım sizin derdiniz olmuyor."),
    ("Sigorta güvencesi var mı?",
     "Var. Kiralama süresince kapsamlı sigorta güvencesiyle çalışıyoruz."),
    ("Nerede bulunuyorsunuz, hangi bölgelere geliyorsunuz?",
     "Depomuz Eyüpsultan'da. İstanbul'un tüm ilçelerine — Avrupa ve Anadolu yakasının "
     "tamamına — kurulum yapıyoruz."),
]

def hakkimizda_sayfasi():
    yol = "/hakkimizda/"
    baslik = f"Hakkımızda — {S['marka']} | İstanbul İskele Kiralama"
    aciklama = ("Deha İskele: 10 yılı aşkın deneyimle İstanbul genelinde iskele kiralama, "
                "kurulum ve söküm. 18 iskele sistemi, sigorta güvencesi, 7/24 teknik destek.")
    sema = (isletme_semasi() + sss_semasi(HAKKIMIZDA_SSS) +
            ldj({"@context": "https://schema.org", "@type": "AboutPage",
                 "name": baslik, "url": ALAN + yol,
                 "mainEntity": {"@id": ALAN + "/#isletme"}}))
    donem = "".join(f'<div class="donem"><h3>{e(a)}</h3><p>{e(b)}</p></div>'
                    for a, b in D.KIRALAMA_DONEMLERI)
    tur_ln = "".join(f'<li><a href="/{t["slug"]}/">{e(t["ad"])}</a></li>' for t in D.TURLER)
    return head(baslik, aciklama, yol, sema) + ust_header(aktif=yol) + f"""
{kirinti([("Ana Sayfa", "/"), ("Hakkımızda", None)])}
<main id="ana">
<section class="hero hero-ic">
  <div class="kap">
    {hero_h1(["Deha İskele Hakkında"])}
    <p class="hero-alt">İstanbul'da 10 yılı aşkın süredir iskele kiralıyoruz. Kurulumdan
       sökümüne kadar işin tamamı bizde; siz sadece kendi işinize bakıyorsunuz.</p>
    <div class="dg-grup">{tel_btn()}{tel2_btn()}{wa_btn()}</div>
  </div>
</section>

{guven_seridi()}

<section class="bol"><div class="kap">{vitrin("istanbul-kiralik-insaat-iskele", oncelik=True)}</div></section>

<section class="bol"><div class="kap dar metin">
  <h2>Biz Kimiz?</h2>
  <p>Deha İskele olarak <strong>10 yılı aşkın sektör deneyimiyle</strong> İstanbul genelinde
     iskele kiralama hizmeti veriyoruz. Depomuz Eyüpsultan'da; ekip iki yakaya da aynı yerden
     çıkıyor.</p>
  <p>Bu işte uzun süre kalmanın bir avantajı var: aynı ölçüdeki iki binanın neden aynı kurulumu
     istemediğini artık keşfe gitmeden tahmin edebiliyoruz :) Dar sokak, eğimli bahçe, bitişik
     nizam, otopark üstü zemin — bunların her biri iskeleyi baştan değiştiriyor. O yüzden
     telefonda kesin fiyat vermek yerine gelip bakmayı tercih ediyoruz.</p>

  <h2>Neden Deha İskele?</h2>
  <ul class="ok-liste">
    <li><strong>Kurulum ve söküm bizde.</strong> Malzemeyi kapınıza bırakıp gitmiyoruz.
        Ekibimiz kuruyor, iş bitince söküp götürüyor.</li>
    <li><strong>Sigorta güvencesi.</strong> Kiralama süresince kapsamlı sigorta kapsamıyla
        çalışıyoruz.</li>
    <li><strong>Her gün açığız.</strong> Pazar dahil 08:30-19:00 arası ulaşabilirsiniz;
        iskelede acil bir durum varsa (fırtına sonrası, bir parça gevşemesi) saat fark
        etmeksizin arayın — 7/24 destek hattımız için bu istisna geçerli.</li>
    <li><strong>Esnek kiralama.</strong> Günlük, haftalık ve aylık seçenekler; iş ne kadar
        sürüyorsa o kadar ödüyorsunuz.</li>
    <li><strong>Her ölçekte iş.</strong> Küçük bir balkon onarımından fabrika bakımına kadar.</li>
  </ul>

  <h2>Kiralama Dönemlerimiz</h2>
</div>
<div class="kap"><div class="izgara-3">{donem}</div></div></section>

<section class="bol"><div class="kap dar metin">
  <h2>Kiraladığımız İskele Sistemleri</h2>
  <p>18 farklı sistem var ve hepsi ayrı bir işe oturuyor. Hangisinin sizin işinize uyduğundan
     emin değilseniz <a href="/iskele-cesitleri/">iskele çeşitleri</a> sayfasındaki
     karşılaştırma tablosuna bakabilir ya da doğrudan arayabilirsiniz.</p>
  <ul class="ilce-liste">{tur_ln}</ul>

  <h2>Nerelere Geliyoruz?</h2>
  <p>İstanbul'un <a href="/ilceler/">tüm ilçelerine</a> — Avrupa ve Anadolu yakasının tamamına.
     İlçenize ait sayfada o bölgede sık karşılaştığımız zemin, sokak ve yapı stoğu notlarını
     bulabilirsiniz.</p>
  <p>{ana_link("Genel hizmet kapsamımız için %s sayfamıza bakabilirsiniz.")}</p>
</div></section>

{tanitim_bolum("Tanıtım Dosyamız")}
{sss_bolum(HAKKIMIZDA_SSS, "Deha İskele Hakkında Sık Sorulanlar")}
{harita_bolum()}
{cta_band("Cephenizi ölçelim, net konuşalım",
          "Kat sayısını ve cephe enini söyleyin; aralığı telefonda verelim, kesin fiyatı keşifte çıkaralım.")}
</main>
{alt_bilgi()}"""


# ── İlçeler sayfası ─────────────────────────────────────────────────────────
# ⚠️ Menüdeki "İlçeler" bağlantısı `#ilceler` çapasıydı; o bölüm YALNIZ anasayfada
#    olduğu için iç sayfalarda hiçbir yere gitmiyordu (kullanıcı bildirdi).
#    39 ilçeye giden gerçek bir hub sayfası açıldı; tüm `/#ilceler` bağlantıları
#    buraya yönlendirildi.
ILCELER_SSS = [
    ("İstanbul'un hangi ilçelerine iskele kiralıyorsunuz?",
     "39 ilçenin tamamına — Avrupa ve Anadolu yakasının hepsine. Depomuz "
     "Eyüpsultan'da, ekip iki yakaya da aynı yerden çıkıyor."),
    ("İlçeme göre fiyat değişiyor mu?",
     "Doğrudan ilçeye göre değil ama erişime göre değişiyor. Dar sokakta kamyon "
     "yanaşamıyorsa malzeme elden taşınıyor, eğimli zeminde ayak kotları ayrı ayrı "
     "ayarlanıyor — bunlar işçiliği etkiliyor. Metrekare aynı olsa da işin zorluğu "
     "farklı oluyor."),
    ("Uzak ilçelere de geliyor musunuz?",
     "Geliyoruz. Şile, Silivri, Çatalca gibi uzak ilçelerde nakliye mesafesi "
     "maliyette görünür bir kalem oluyor; onu da baştan konuşuyoruz. Ekip tek "
     "programda gidip işi bitirecek şekilde planlanıyor."),
]

def ilceler_sayfasi():
    yol = "/ilceler/"
    h1 = f"İstanbul İlçeleri İskele Kiralama - {S['marka']}"
    aciklama = ("İstanbul'un 39 ilçesinde cephe iskelesi kiralama, kurulum ve söküm. "
                "Eyüpsultan merkezli ekip, Avrupa ve Anadolu yakasının tamamına hizmet.")
    sema = (isletme_semasi() + sss_semasi(ILCELER_SSS) +
            ldj({"@context": "https://schema.org", "@type": "CollectionPage",
                 "name": h1, "url": ALAN + yol,
                 "about": {"@id": ALAN + "/#isletme"}}))
    return head(h1, aciklama, yol, sema) + ust_header(aktif=yol) + f"""
{kirinti([("Ana Sayfa", "/"), ("İlçeler", None)])}
<main id="ana">
<section class="hero hero-ic">
  <div class="kap">
    {hero_h1([h1])}
    <p class="hero-slogan">İstanbul'un 39 ilçesinin tamamı</p>
    <p class="hero-alt">Depomuz {e(S['adres_ilce'])}'da; ekip Avrupa ve Anadolu yakasına
       aynı yerden çıkıyor. İlçenize ait sayfada o bölgede sık karşılaştığımız zemin,
       sokak ve yapı stoğu notlarını bulabilirsiniz.</p>
    <div class="dg-grup">{tel_btn()}{teklif_btn("dg dg-cerceve")}</div>
  </div>
</section>

{guven_seridi()}
{ilce_agi("Hizmet Verdiğimiz İlçeler")}

<section class="bol"><div class="kap dar metin">
  <h2>İlçe Fark Eder mi?</h2>
  <p>Fiyat açısından doğrudan etmiyor ama iş açısından çok ediyor :) Aynı ölçüdeki iki
     bina, sokağı ve zemini farklı olduğu için aynı kurulumu istemiyor. Fatih'te sokak
     genişliği üç metrenin altına inebiliyor, Sarıyer'de bahçe eğimli, Beylikdüzü'nde
     iskele otopark döşemesinin üstüne kuruluyor.</p>
  <p>Bu yüzden her ilçe için ayrı sayfa yazdık — orada o bölgede sık karşılaştığımız
     durumları anlattık. Kendi ilçenizi listeden seçip bakabilirsiniz.</p>
  <p>{ana_link("Genel hizmet kapsamımız için %s sayfamıza bakabilirsiniz.")}</p>
</div></section>

{sss_bolum(ILCELER_SSS, "İlçeler Hakkında Sık Sorulanlar")}
{harita_bolum()}
{cta_band("İlçenizde iskele mi gerekiyor?",
          "Kat sayısını ve cephe enini söyleyin; aralığı telefonda verelim, kesin fiyatı keşifte çıkaralım.")}
</main>
{alt_bilgi()}"""

# ── Yazıcı ──────────────────────────────────────────────────────────────────

def ritim_uygula(sayfa):
    """Bölüm zeminlerini beyaz/gri DÖNÜŞÜMLÜ yapar.
    ⚠️ Sınıf bazlı boyama (.turler gri, .hesap beyaz…) yetmiyordu: tür, ilçe ve
       rehber sayfalarında bölüm dizilimi farklı olduğu için 2-4 aynı zemin arka
       arkaya geliyor, sayfa "oturaksız" görünüyordu (kullanıcı bildirdi).
       Zemin artık sayfadaki SIRAYA göre veriliyor, her sayfa tipinde tutarlı.
    ⛔ Bölüm zeminini CSS'te sınıf adıyla ezme — ritmi bozar."""
    sayac = [0]
    def degis(m):
        sinif = m.group(1)
        if sinif.startswith("bolunmus"):
            # Kendi rengi var (beyaz) ama SAYACI ARTIRIR — yoksa ardından gelen
            # bölüm de beyaz düşüp iki beyaz zemin arka arkaya geliyor.
            sayac[0] += 1
            return m.group(0)
        if any(x in sinif for x in ("serit", "cta", "hero")):
            return m.group(0)
        sayac[0] += 1
        return '<section class="%s %s"' % (sinif, "bol-gri" if sayac[0] % 2 else "bol-ak")
    return re.sub(r'<section class="((?:bol|bolunmus)\b[^"]*)"', degis, sayfa)

def yaz(yol, ic):
    ic = ritim_uygula(ic)
    if yol == "/":
        hedef = os.path.join(KOK, "index.html")
    elif yol.endswith("/"):
        hedef = os.path.join(KOK, yol.strip("/"), "index.html")
    else:
        hedef = os.path.join(KOK, yol.lstrip("/"))
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    with open(hedef, "w", encoding="utf-8") as f:
        f.write(ic)

def hata404():
    baslik = "Sayfa bulunamadı | " + S["marka"]
    aciklama = ("Aradığınız sayfa taşınmış ya da hiç var olmamış olabilir. İskele kiralama "
                "hizmetimiz için ana sayfaya dönebilir veya doğrudan arayabilirsiniz.")
    ilk = "".join(f'<li><a href="/{t["slug"]}/">{e(t["ad"])}</a></li>' for t in D.TURLER[:5])
    return head(baslik, aciklama, "/404.html") + ust_header() + f"""
<main id="ana">
<section class="hero hero-ic">
  <div class="kap">
    {hero_h1(["Sayfa bulunamadı"])}
    <p class="hero-alt">Aradığınız sayfa taşınmış olabilir. Aşağıdan devam edebilir ya da
       doğrudan arayabilirsiniz.</p>
    <div class="dg-grup">{tel_btn()}{wa_btn()}</div>
  </div>
</section>
<section class="bol"><div class="kap dar metin">
  <h2>Sık kullanılan sayfalar</h2>
  <ul class="ok-liste">{ilk}
    <li><a href="/iskele-kiralama-fiyatlari/">İskele kiralama fiyatları</a></li>
    <li><a href="/ilceler/">İstanbul ilçeleri</a></li>
  </ul>
</div></section>
</main>
{alt_bilgi()}"""

def sitemap(yollar):
    g = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for y, oncelik in yollar:
        g.append(f"  <url><loc>{ALAN}{y}</loc><priority>{oncelik}</priority></url>")
    g.append("</urlset>")
    return "\n".join(g) + "\n"

def main():
    yollar = []
    yaz("/", anasayfa());                    yollar.append(("/", "1.0"))
    for i in D.ILCELER:
        yaz(ilce_yolu(i), ilce_sayfasi(i));  yollar.append((ilce_yolu(i), "0.8"))
    for t in D.TURLER:
        yaz(f'/{t["slug"]}/', tur_sayfasi(t)); yollar.append((f'/{t["slug"]}/', "0.9"))
    for r in D.REHBERLER:
        yaz(f'/{r["slug"]}/', rehber_sayfasi(r)); yollar.append((f'/{r["slug"]}/', "0.7"))
    yaz("/hakkimizda/", hakkimizda_sayfasi()); yollar.append(("/hakkimizda/", "0.9"))
    yaz("/ilceler/", ilceler_sayfasi()); yollar.append(("/ilceler/", "0.9"))
    yaz("/404.html", hata404())

    with open(os.path.join(KOK, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap(yollar))
    with open(os.path.join(KOK, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % ALAN)
    with open(os.path.join(KOK, "CNAME"), "w", encoding="utf-8") as f:
        f.write(ALAN.split("//")[1] + "\n")

    print(f"{len(yollar)} sayfa yazıldı  (1 ana + {len(D.ILCELER)} ilçe + "
          f"{len(D.TURLER)} tür + {len(D.REHBERLER)} rehber)")
    if not D.FIYATLAR:
        print("⏳ UYARI: data.FIYATLAR boş — fiyat tablosu basılmadı.")
    if len(D.ONAYLI_IDDIALAR) < 2:
        print("⏳ UYARI: ONAYLI_IDDIALAR listesi zayıf — tecrübe/sigorta/belge teyidi bekleniyor.")

if __name__ == "__main__":
    main()
