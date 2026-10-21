/* The entry-page photo carousel: arrows, a thumbnail track, and swipe.

   The stage is a flex row moved with `transform: translateX(-n * 100%)`, and
   the current index is a plain variable. It began as a CSS scroll-snap
   scroller -- which is prettier in principle, since the browser does the
   swiping and the scroll position IS the state -- and that was abandoned
   after it proved unworkable here: with `scroll-snap-type: x mandatory`, a
   programmatic scroll gets re-snapped back to where it started, so the
   arrows updated the counter while the picture never moved. Transform has no
   browser scrolling behaviour to fight, so it simply does what it is told.

   Swipe is therefore implemented by hand, from pointer events: a horizontal
   drag past a threshold moves one slide. */
(function () {
  "use strict";

  document.querySelectorAll("[data-carousel]").forEach(function (root) {
    var rail = root.querySelector(".carousel-rail");
    var slides = Array.prototype.slice.call(root.querySelectorAll(".carousel-slide"));
    var dots = Array.prototype.slice.call(root.querySelectorAll(".carousel-dot"));
    var track = root.querySelector(".carousel-track");
    var caption = root.querySelector(".carousel-caption");
    var counter = root.querySelector(".carousel-counter");
    var prev = root.querySelector(".carousel-prev");
    var next = root.querySelector(".carousel-next");
    if (!rail || slides.length === 0) return;

    var index = 0;

    function credit(d) {
      var lic = d.licence
        ? (d.licenceUrl ? '<a href="' + d.licenceUrl + '">' + d.licence + "</a>" : d.licence)
        : "";
      var src = d.source ? '<a href="' + d.source + '">Wikimedia Commons</a>' : "";
      return [d.author, lic, src].filter(Boolean).join(" · ");
    }

    /* Keep the selected thumbnail visible by setting the track's own
       scrollLeft, and only when it is outside the strip. Never
       scrollIntoView: it scrolls every scrollable ancestor including the
       page, and an earlier version that used it locked the renderer. */
    function revealDot(i) {
      if (!track || !dots[i]) return;
      var d = dots[i];
      var left = d.offsetLeft - track.offsetLeft;
      var right = left + d.offsetWidth;
      if (left < track.scrollLeft) track.scrollLeft = left;
      else if (right > track.scrollLeft + track.clientWidth) {
        track.scrollLeft = right - track.clientWidth;
      }
    }

    function render() {
      rail.style.transform = "translateX(" + (-index * 100) + "%)";
      slides.forEach(function (s, n) {
        /* Slides that are off-stage must not be reachable by Tab. */
        s.querySelector(".gallery-item").tabIndex = n === index ? 0 : -1;
        s.setAttribute("aria-hidden", n === index ? "false" : "true");
      });
      dots.forEach(function (b, n) {
        var on = n === index;
        b.classList.toggle("is-current", on);
        b.setAttribute("aria-current", on ? "true" : "false");
      });
      if (counter) counter.textContent = index + 1 + " / " + slides.length;
      if (caption) {
        var d = slides[index].querySelector(".gallery-item").dataset;
        caption.innerHTML =
          (d.caption ? '<span class="carousel-text">' + d.caption + "</span>" : "") +
          '<span class="carousel-credit">' + credit(d) + "</span>";
      }
      revealDot(index);
    }

    function go(i) {
      index = Math.max(0, Math.min(slides.length - 1, i));
      render();
    }

    if (prev) prev.addEventListener("click", function () { go(index - 1); });
    if (next) next.addEventListener("click", function () { go(index + 1); });
    dots.forEach(function (b) {
      b.addEventListener("click", function () { go(parseInt(b.dataset.index, 10)); });
    });

    /* Arrow keys move the carousel only while it has focus, so they do not
       fight the lightbox or the page. */
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); go(index - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(index + 1); }
    });

    /* Swipe. A drag is only claimed once it is clearly horizontal, so a
       vertical flick still scrolls the page. */
    var startX = 0, startY = 0, dragging = false, decided = false, horizontal = false;
    rail.addEventListener("pointerdown", function (e) {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      dragging = true; decided = false; horizontal = false;
      startX = e.clientX; startY = e.clientY;
    });
    rail.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      var dx = e.clientX - startX;
      var dy = e.clientY - startY;
      if (!decided && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
        decided = true;
        horizontal = Math.abs(dx) > Math.abs(dy);
      }
      if (horizontal) e.preventDefault();
    });
    function endDrag(e) {
      if (!dragging) return;
      dragging = false;
      if (!horizontal) return;
      var dx = e.clientX - startX;
      if (Math.abs(dx) > 40) go(index + (dx < 0 ? 1 : -1));
    }
    rail.addEventListener("pointerup", endDrag);
    rail.addEventListener("pointercancel", function () { dragging = false; });

    render();
  });
})();
