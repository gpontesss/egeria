/* The entry-page photo carousel.

   The stage is a scroll-snap row, so the browser does the swiping, the
   momentum and the snapping, and the scroll position IS the state -- this
   file only reads it and nudges it. That is why there is no transform
   animation, no index variable to keep in sync with the DOM, and why it
   still works if this script never loads: the slides remain a scrollable
   row of photographs. */
(function () {
  "use strict";

  document.querySelectorAll("[data-carousel]").forEach(function (root) {
    var stage = root.querySelector(".carousel-slides");
    var slides = Array.prototype.slice.call(root.querySelectorAll(".carousel-slide"));
    var dots = Array.prototype.slice.call(root.querySelectorAll(".carousel-dot"));
    var caption = root.querySelector(".carousel-caption");
    var counter = root.querySelector(".carousel-counter");
    var prev = root.querySelector(".carousel-prev");
    var next = root.querySelector(".carousel-next");
    if (!stage || slides.length === 0) return;

    function current() {
      /* Nearest slide to the stage's left edge, which survives a partial
         swipe and a resize without any stored index. */
      var x = stage.scrollLeft;
      var best = 0;
      var bestD = Infinity;
      slides.forEach(function (s, i) {
        var d = Math.abs(s.offsetLeft - stage.offsetLeft - x);
        if (d < bestD) { bestD = d; best = i; }
      });
      return best;
    }

    function credit(d) {
      var lic = d.licence
        ? (d.licenceUrl ? '<a href="' + d.licenceUrl + '">' + d.licence + "</a>" : d.licence)
        : "";
      var src = d.source ? '<a href="' + d.source + '">Wikimedia Commons</a>' : "";
      return [d.author, lic, src].filter(Boolean).join(" · ");
    }

    function sync() {
      var i = current();
      dots.forEach(function (b, n) {
        var on = n === i;
        b.classList.toggle("is-current", on);
        b.setAttribute("aria-current", on ? "true" : "false");
      });
      if (counter) counter.textContent = i + 1 + " / " + slides.length;
      if (caption) {
        var d = slides[i].querySelector(".gallery-item").dataset;
        caption.innerHTML =
          (d.caption ? '<span class="carousel-text">' + d.caption + "</span>" : "") +
          '<span class="carousel-credit">' + credit(d) + "</span>";
      }
      if (dots[i]) {
        /* Keep the selected thumbnail in view in its own scroller, without
           dragging the page about: nearest, and on the inline axis only. */
        dots[i].scrollIntoView({ block: "nearest", inline: "nearest" });
      }
    }

    function go(i) {
      var n = Math.max(0, Math.min(slides.length - 1, i));
      stage.scrollTo({ left: slides[n].offsetLeft - stage.offsetLeft, behavior: "smooth" });
      /* Smooth scrolling can silently no-op; sync from the scroll handler
         when it works, and from here after a beat when it does not. */
      setTimeout(sync, 350);
    }

    if (prev) prev.addEventListener("click", function () { go(current() - 1); });
    if (next) next.addEventListener("click", function () { go(current() + 1); });
    dots.forEach(function (b) {
      b.addEventListener("click", function () { go(parseInt(b.dataset.index, 10)); });
    });

    var ticking = false;
    stage.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () { sync(); ticking = false; });
    }, { passive: true });

    /* Arrow keys move the carousel only while it has focus, so they do not
       fight the lightbox or the page. */
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); go(current() - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(current() + 1); }
    });

    window.addEventListener("resize", sync);
    sync();
  });
})();
