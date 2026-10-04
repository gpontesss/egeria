/* Gallery lightbox: open a photograph large, with the credit that its licence
   requires, and move between them with the arrow keys.

   No dependency and no markup duplication -- every frame's data lives on the
   button that opens it, and one overlay is reused for all of them. */
(function () {
  "use strict";

  var items = Array.prototype.slice.call(document.querySelectorAll(".gallery-item"));
  if (!items.length) return;

  var overlay = document.createElement("div");
  overlay.className = "lightbox";
  overlay.hidden = true;
  overlay.innerHTML =
    '<button class="lightbox-close" type="button" aria-label="Close">×</button>' +
    '<button class="lightbox-prev" type="button" aria-label="Previous photograph">‹</button>' +
    '<figure class="lightbox-figure">' +
    '<img alt="">' +
    '<figcaption><span class="lightbox-caption"></span><span class="lightbox-credit"></span></figcaption>' +
    "</figure>" +
    '<button class="lightbox-next" type="button" aria-label="Next photograph">›</button>';
  document.body.appendChild(overlay);

  var img = overlay.querySelector("img");
  var capEl = overlay.querySelector(".lightbox-caption");
  var creditEl = overlay.querySelector(".lightbox-credit");
  var current = 0;
  var opener = null;

  function credit(d) {
    var lic = d.licence
      ? (d.licenceUrl
          ? '<a href="' + d.licenceUrl + '">' + d.licence + "</a>"
          : d.licence)
      : "";
    var src = d.source ? '<a href="' + d.source + '">Wikimedia Commons</a>' : "";
    return [d.author, lic, src].filter(Boolean).join(" · ");
  }

  function show(i) {
    current = (i + items.length) % items.length;
    var d = items[current].dataset;
    img.src = d.full;
    img.alt = d.caption || items[current].querySelector("img").alt;
    capEl.textContent = d.caption || "";
    creditEl.innerHTML = credit(d);
  }

  function open(i, from) {
    opener = from || null;
    show(i);
    overlay.hidden = false;
    document.body.classList.add("lightbox-open");
    overlay.querySelector(".lightbox-close").focus();
  }

  function close() {
    overlay.hidden = true;
    document.body.classList.remove("lightbox-open");
    img.removeAttribute("src");
    if (opener) opener.focus();
  }

  items.forEach(function (btn, i) {
    btn.addEventListener("click", function () { open(i, btn); });
  });

  overlay.addEventListener("click", function (e) {
    if (e.target.closest(".lightbox-close")) return close();
    if (e.target.closest(".lightbox-prev")) return show(current - 1);
    if (e.target.closest(".lightbox-next")) return show(current + 1);
    /* A click on the backdrop closes; a click on the picture or its caption
       does not, so selecting the credit text does not shut the overlay. */
    if (!e.target.closest(".lightbox-figure")) close();
  });

  document.addEventListener("keydown", function (e) {
    if (overlay.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") show(current - 1);
    else if (e.key === "ArrowRight") show(current + 1);
  });
})();
