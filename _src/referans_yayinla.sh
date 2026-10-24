#!/bin/bash
# Panelden gelen referansları siteye yayınlar. systemd: dehaiskele-referans.path → .service (root).
# Panel (panel8784) yalnız veri/yayinla.istek dosyasına dokunur; GitHub anahtarına erişimi yok.
# Sonuç veri/yayin-durum.json'a yazılır, panel üst bilgide gösterir.
set -uo pipefail
REPO=/root/dehaiskele
V=/home/panel.dehaiskele.com/veri
U=panel8194
exec 9>/run/dehaiskele-referans.lock
flock 9
sleep 5   # art arda yapılan düzenlemeleri tek yayında topla

durum() {  # durum <ok|hata> <mesaj>
  python3 - "$1" "$2" "$V/yayin-durum.json" <<'PY'
import json, sys, datetime
json.dump({"durum": sys.argv[1], "mesaj": sys.argv[2][-400:],
           "zaman": datetime.datetime.now().astimezone().isoformat(timespec="seconds")},
          open(sys.argv[3], "w"), ensure_ascii=False)
PY
  chown $U:$U "$V/yayin-durum.json"; chmod 600 "$V/yayin-durum.json"
}
hata() { echo "HATA: $1" >&2; durum hata "$1"; exit 1; }

cd "$REPO" || hata "depo yok"
git pull -q --rebase --autostash origin main 2>&1 || hata "git pull başarısız"
python3 _src/referans_al.py "$V" || hata "referans verisi okunamadı"
python3 _src/media.py --referans >/dev/null || hata "görsel türevleri üretilemedi"
python3 _src/build.py >/dev/null || hata "site üretilemedi"
python3 _src/denetim.py >/tmp/dehaiskele-denetim.txt || hata "denetim: $(grep HATA /tmp/dehaiskele-denetim.txt | head -3 | tr '\n' ' ')"
# ⚠️ Yalnız referans + üretilen çıktılar eklenir; depoda yarım kalmış kaynak düzenlemesi varsa ona dokunulmaz.
git add _src/referanslar.json img/referans images/referans sitemap.xml '*.html' 2>/dev/null
if git diff --cached --quiet; then durum ok "değişiklik yok"; exit 0; fi
git commit -q -m "Referanslar panelden güncellendi" || hata "commit başarısız"
git push -q origin HEAD:main 2>&1 || hata "GitHub'a gönderilemedi"
durum ok "yayınlandı $(git rev-parse --short HEAD)"
echo "yayınlandı"
