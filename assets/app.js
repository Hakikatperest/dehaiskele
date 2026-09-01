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
    });
    menu.addEventListener("click", function (o) {
      if (o.target.tagName === "A") {
        menu.classList.remove("acik");
        ham.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", function (o) {
      if (o.key === "Escape" && menu.classList.contains("acik")) {
        menu.classList.remove("acik");
        ham.setAttribute("aria-expanded", "false");
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
