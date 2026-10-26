/* dehaiskele.com — kütüphane yok, tek dosya. */
(function () {
  "use strict";

  /* ── Mobil menü ─────────────────────────────────────────────────────── */
  var ham = document.getElementById("hamburger"),
      menu = document.getElementById("menu");
  if (ham && menu) {
    ham.addEventListener("click", function () {
      var acik = menu.classList.toggle("acik");
      ham.setAttribute("aria-expanded", acik ? "true" : "false");
      ham.setAttribute("aria-label", acik ? "Menüyü kapat" : "Menüyü aç");
      /* Menü açıkken sabit alt çubuk gizlensin — menünün altını örtüyordu. */
      document.body.classList.toggle("menu-acik", acik);
    });
    menu.addEventListener("click", function (o) {
      if (o.target.tagName === "A") {
        menu.classList.remove("acik");
        ham.setAttribute("aria-expanded", "false");
        document.body.classList.remove("menu-acik");
      }
    });
    document.addEventListener("keydown", function (o) {
      if (o.key === "Escape" && menu.classList.contains("acik")) {
        menu.classList.remove("acik");
        ham.setAttribute("aria-expanded", "false");
        document.body.classList.remove("menu-acik");
        ham.focus();
      }
    });
  }

  /* ── Hero satır açılışı ─────────────────────────────────────────────── */
  var hb = document.querySelector(".hb");
  if (hb) requestAnimationFrame(function () { hb.classList.add("ac"); });

  /* ── Ortaya çıkış ────────────────────────────────────────────────────
     ⚠️ Güvenlik ağı şart: IntersectionObserver bir sebeple tetiklenmezse
        içerik kalıcı olarak gizli kalıyor (seyrannakliyat'ta beyaz ekran). */
  var gelenler = document.querySelectorAll(".gel");
  if (gelenler.length) {
    if ("IntersectionObserver" in window) {
      var goz = new IntersectionObserver(function (girisler) {
        girisler.forEach(function (g) {
          if (g.isIntersecting) {
            var kap = g.target.parentNode, kardesler, n = 0;
            if (kap) {
              kardesler = kap.querySelectorAll(":scope > .gel");
              n = Array.prototype.indexOf.call(kardesler, g.target);
            }
            g.target.style.transitionDelay = Math.min(n, 6) * 55 + "ms";
            g.target.classList.add("gorundu");
            goz.unobserve(g.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.02 });
      gelenler.forEach(function (x) { goz.observe(x); });
      setTimeout(function () {
        gelenler.forEach(function (x) {
          if (!x.classList.contains("gorundu") &&
              x.getBoundingClientRect().top < window.innerHeight * 1.5) {
            x.classList.add("gorundu");
          }
        });
      }, 2500);
    } else {
      gelenler.forEach(function (x) { x.classList.add("gorundu"); });
    }
  }

  /* ── Cephe metrekaresi hesaplayıcı ──────────────────────────────────── */
  var en = document.getElementById("h-en"),
      kat = document.getElementById("h-kat"),
      yuk = document.getElementById("h-yuk"),
      cikti = document.getElementById("h-sonuc");
  if (en && kat && yuk && cikti) {
    var say = function (x) { return x.toLocaleString("tr-TR", { maximumFractionDigits: 1 }); };
    var hesapla = function () {
      var e = parseFloat(en.value) || 0,
          k = parseInt(kat.value, 10) || 0,
          y = parseFloat(yuk.value) || 0,
          h = k * y,
          m2 = e * h;
      if (m2 <= 0) { cikti.textContent = "Ölçüleri girin, metrekareyi hesaplayalım."; return; }
      cikti.innerHTML =
        "Bina yüksekliği yaklaşık <b>" + say(h) + " m</b> · " +
        "iskele alanı <b>" + say(m2) + " m²</b>" +
        "<br><small>Tek cephe için. Birden fazla cephe kurulacaksa her birini ayrı hesaplayıp " +
        "toplayın. Balkon, çıkma ve zemin kotu farkı bu rakamı değiştirir.</small>";
    };
    [en, kat, yuk].forEach(function (x) { x.addEventListener("input", hesapla); });
    hesapla();
  }

  /* ── Harita facade — iframe ancak tıklanınca ────────────────────────── */
  document.querySelectorAll(".harita").forEach(function (kutu) {
    var dg = kutu.querySelector(".harita-ac");
    if (!dg) return;
    dg.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = kutu.getAttribute("data-src");
      f.title = "Deha İskele konumu — Google Haritalar";
      f.loading = "lazy";
      f.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
      f.setAttribute("allowfullscreen", "");
      kutu.innerHTML = "";
      kutu.appendChild(f);
    });
  });
})();

/* PDF facade — gömülü görüntüleyici ancak tıklanınca yükleniyor.
   ⚠️ iOS Safari gömülü PDF'i düzgün göstermiyor; orada yeni sekmede açıyoruz. */
(function () {
  "use strict";
  document.querySelectorAll(".pdf-kutu").forEach(function (kutu) {
    var dg = kutu.querySelector(".pdf-ac");
    if (!dg) return;
    dg.addEventListener("click", function () {
      var src = kutu.getAttribute("data-pdf");
      var ios = /iP(hone|ad|od)/.test(navigator.userAgent);
      if (ios) { window.open(src, "_blank", "noopener"); return; }
      var o = document.createElement("object");
      o.data = src; o.type = "application/pdf";
      o.setAttribute("aria-label", "Deha İskele firma tanıtım dosyası");
      var yedek = document.createElement("p");
      yedek.className = "pdf-yedek";
      yedek.innerHTML = 'Tarayıcınız gömülü PDF göstermiyor. ' +
        '<a href="' + src + '" target="_blank" rel="noopener">Dosyayı yeni sekmede açın</a>.';
      o.appendChild(yedek);
      kutu.classList.add("acik");
      kutu.innerHTML = "";
      kutu.appendChild(o);
    });
  });
})();

/* Kaydırınca üst menü kompaktlaşsın — yalnız sınıf değişiyor, iş CSS'te.
   passive dinleyici + rAF: kaydırma performansına dokunmuyor. */
(function () {
  "use strict";
  /* ⚠️ Histerezis: tek eşik kullanılırsa sınır civarında sınıf açılıp kapanıyor.
     Açılış 90px, kapanış 40px — arada 50px'lik ölü bant var. */
  var ac = 90, kapa = 40, bekle = false, durum = false;
  function bak() {
    var y = window.scrollY;
    if (!durum && y > ac) { durum = true; document.body.classList.add("kaydi"); }
    else if (durum && y < kapa) { durum = false; document.body.classList.remove("kaydi"); }
    bekle = false;
  }
  window.addEventListener("scroll", function () {
    if (!bekle) { bekle = true; requestAnimationFrame(bak); }
  }, { passive: true });
  bak();
})();

/* Işık kutusu — [data-buyut] bağlantıları büyük görseli tam ekran açar.
   JS yoksa bağlantı görseli doğrudan açar (yedek davranış). Kütüphane yok.
   ⚠️ Kaydırma kilidi YALNIZ html'de (body overflow sticky başlığı öldürür). */
(function () {
  "use strict";
  var bag = document.querySelectorAll("[data-buyut]");
  if (!bag.length) return;
  var kutu = document.createElement("div"), son = null;
  kutu.className = "isik";
  kutu.setAttribute("role", "dialog");
  kutu.setAttribute("aria-modal", "true");
  kutu.setAttribute("aria-label", "Büyütülmüş görsel");
  kutu.innerHTML = '<button class="isik-kapat" type="button" aria-label="Kapat">&times;</button><img alt="">' +
    '<button class="isik-ok isik-geri" type="button" aria-label="Önceki görsel">&#8249;</button>' +
    '<button class="isik-ok isik-ileri" type="button" aria-label="Sonraki görsel">&#8250;</button>' +
    '<span class="isik-sayac" aria-live="polite"></span>';
  document.body.appendChild(kutu);
  var img = kutu.querySelector("img"), kapatDg = kutu.querySelector(".isik-kapat"),
      geriDg = kutu.querySelector(".isik-geri"), ileriDg = kutu.querySelector(".isik-ileri"),
      sayac = kutu.querySelector(".isik-sayac"), grup = [], sira = 0;
  // Galeri: aynı data-galeri değerine sahip bağlantılar (referans başına 1–5 görsel) ileri/geri gezilir.
  function goster(n) {
    sira = (n + grup.length) % grup.length;
    var a = grup[sira], k = a.querySelector("img");
    img.src = a.getAttribute("href");
    img.alt = k ? k.alt : "";
    var cok = grup.length > 1;
    geriDg.hidden = ileriDg.hidden = sayac.hidden = !cok;
    sayac.textContent = cok ? (sira + 1) + " / " + grup.length : "";
  }
  geriDg.addEventListener("click", function (o) { o.stopPropagation(); goster(sira - 1); });
  ileriDg.addEventListener("click", function (o) { o.stopPropagation(); goster(sira + 1); });
  var dokunX = null;
  kutu.addEventListener("touchstart", function (o) { dokunX = o.touches[0].clientX; }, { passive: true });
  kutu.addEventListener("touchend", function (o) {
    if (dokunX === null || grup.length < 2) return;
    var fark = o.changedTouches[0].clientX - dokunX; dokunX = null;
    if (Math.abs(fark) > 50) goster(sira + (fark < 0 ? 1 : -1));
  });
  function kapat() {
    kutu.classList.remove("acik");
    document.documentElement.classList.remove("isik-kilit");
    setTimeout(function () { if (!kutu.classList.contains("acik")) img.removeAttribute("src"); }, 250);
    if (son) son.focus();
  }
  bag.forEach(function (a) {
    a.addEventListener("click", function (o) {
      if (o.metaKey || o.ctrlKey || o.shiftKey) return;   // yeni sekmede açmak isteyene dokunma
      o.preventDefault();
      son = a;
      var g = a.getAttribute("data-galeri");
      grup = g ? Array.prototype.filter.call(bag, function (x) { return x.getAttribute("data-galeri") === g; }) : [a];
      goster(grup.indexOf(a));
      kutu.classList.add("acik");
      document.documentElement.classList.add("isik-kilit");
      kapatDg.focus();
    });
  });
  kutu.addEventListener("click", function (o) { if (o.target === kutu || o.target === kapatDg) kapat(); });
  document.addEventListener("keydown", function (o) {
    if (!kutu.classList.contains("acik")) return;
    if (o.key === "Escape") kapat();
    if (o.key === "ArrowLeft" && grup.length > 1) goster(sira - 1);
    if (o.key === "ArrowRight" && grup.length > 1) goster(sira + 1);
    if (o.key === "Tab") { o.preventDefault(); kapatDg.focus(); }
  });
})();
