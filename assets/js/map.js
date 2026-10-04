/* Leaflet maps, driven entirely by data attributes on .map containers so that
   no page carries an inline script.

   Two variants:
     data-map="single"    one pin, from data-lat/data-lon
     data-map="overview"  every pin, fetched from data-src (/sites.json)

   Markers are circleMarkers rather than the default pin image: it keeps the
   map monochrome like the rest of the site, and means no marker PNGs are
   needed from the vendored Leaflet. */
(function () {
  "use strict";

  if (typeof L === "undefined") return;

  /* The theme can be the system's or the reader's explicit choice, so read
     the attribute theme.js sets first and fall back to the media query --
     never the media query alone, or a toggled page gets the wrong markers.
     Every marker is kept so they can be restyled when the theme changes. */
  var markers = [];

  function isDark() {
    var chosen = document.documentElement.getAttribute("data-theme");
    if (chosen === "dark") return true;
    if (chosen === "light") return false;
    return !!(
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    );
  }

  function styles() {
    return isDark()
      ? { color: "#000000", fillColor: "#ffffff" }
      : { color: "#ffffff", fillColor: "#000000" };
  }

  document.addEventListener("egeria:theme", function () {
    var s = styles();
    markers.forEach(function (m) {
      m.setStyle({ color: s.color, fillColor: s.fillColor });
    });
  });

  /* The basemap is already grey, so nothing here picks a second URL by
     theme; style.css inverts the tile pane for dark mode. Labels are a
     separate overlay layer where the provider offers one. */
  function basemap(el, map) {
    var maxZoom = parseInt(el.dataset.tilesMaxZoom, 10) || 18;
    L.tileLayer(el.dataset.tiles, {
      attribution: el.dataset.attribution,
      maxZoom: maxZoom
    }).addTo(map);
    if (el.dataset.tilesLabels) {
      L.tileLayer(el.dataset.tilesLabels, { maxZoom: maxZoom }).addTo(map);
    }
    return maxZoom;
  }

  /* Labels are drawn under the pins so a point is identifiable without
     clicking it. They are permanent above LABEL_ZOOM and revert to hover
     tooltips below it: at the overview's opening zoom the whole Aegean is in
     frame and forty-odd permanent labels would overlap into noise. Region
     maps open above the threshold, so they are labelled by default. */
  var LABEL_ZOOM = 11;

  /* The wheel zooms the map. The cost is that a page scroll started over a
     map is captured by it, so the map also has to be able to give the page
     back: see releaseAtBounds below. wheelPxPerZoomLevel is raised from
     Leaflet's default of 60 because at 60 a single trackpad flick crosses
     three or four zoom levels. */
  var WHEEL_ZOOM = {
    zoomControl: true,
    scrollWheelZoom: true,
    wheelPxPerZoomLevel: 160,
    wheelDebounceTime: 50
  };

  /* Once the map can go no further in the direction being scrolled, hand the
     wheel back to the page -- otherwise a map at full zoom-out is a dead spot
     that the reader cannot scroll past without routing around it. */
  function releaseAtBounds(el, map) {
    el.addEventListener("wheel", function (e) {
      var out = e.deltaY > 0;
      var stuck = out
        ? map.getZoom() <= map.getMinZoom()
        : map.getZoom() >= map.getMaxZoom();
      if (stuck) {
        map.scrollWheelZoom.disable();
        /* Re-arm once the wheel is quiet, so the map is usable again when
           the reader comes back to it. */
        clearTimeout(el._wheelRelease);
        el._wheelRelease = setTimeout(function () {
          map.scrollWheelZoom.enable();
        }, 500);
      }
    }, { passive: true });
  }

  function labelText(title) {
    /* Parentheses carry the alternative name, which is what makes these
       titles long; the label wants the short form. */
    var s = String(title).replace(/\s*\([^)]*\)/g, "").trim() || String(title);
    return s.length > 34 ? s.slice(0, 33).replace(/[\s,;:-]+$/, "") + "\u2026" : s;
  }

  function bindLabel(m, title, radius, permanent) {
    if (m.getTooltip()) m.unbindTooltip();      // `permanent` is fixed at bind time
    m.bindTooltip(labelText(title), {
      permanent: !!permanent,
      direction: permanent ? "bottom" : "top",
      offset: [0, permanent ? radius + 1 : -radius],
      opacity: 1,
      className: permanent ? "map-label" : ""
    });
  }

  /* Rebinding every tooltip is only worth doing when the threshold is
     actually crossed, not on every wheel notch. */
  function followZoom(map, entries) {
    var on = null;
    function sync() {
      var want = map.getZoom() >= LABEL_ZOOM;
      if (want === on) return;
      on = want;
      entries.forEach(function (e) { bindLabel(e.marker, e.title, e.radius, want); });
    }
    map.on("zoomend", sync);
    sync();
  }

  /* Hovering a pin opens its popup; clicking one pins it open.

     The delay is the whole trick. Closing on `mouseout` alone makes the
     popup impossible to use -- it vanishes the moment the pointer leaves the
     pin, so the link inside it can never be reached. Instead a close is
     scheduled and then cancelled if the pointer arrives in the popup, which
     is what makes the gap between pin and popup crossable. */
  function hoverPopups(map, entries) {
    var timer = null;
    var pinned = false;

    function cancel() {
      if (timer) { clearTimeout(timer); timer = null; }
    }

    function later() {
      cancel();
      timer = setTimeout(function () {
        if (!pinned) map.closePopup();
      }, 280);
    }

    entries.forEach(function (e) {
      e.marker.on("mouseover", function () {
        cancel();
        if (!e.marker.isPopupOpen()) {
          pinned = false;
          e.marker.openPopup();
        }
      });
      e.marker.on("mouseout", later);
      /* A click keeps it open, so a popup reached deliberately does not
         evaporate while the reader is reading it. */
      e.marker.on("click", function () {
        pinned = true;
        e.marker.openPopup();
      });
    });

    map.on("popupopen", function (ev) {
      var el = ev.popup.getElement();
      if (!el) return;
      el.addEventListener("mouseenter", cancel);
      el.addEventListener("mouseleave", later);
    });
    map.on("popupclose", function () {
      pinned = false;
      cancel();
    });
  }

  function marker(site, radius) {
    var s = styles();
    var m = L.circleMarker([site.lat, site.lon], {
      radius: radius,
      weight: 2,
      color: s.color,
      fillColor: s.fillColor,
      fillOpacity: 1
    });
    /* The photograph sits in its own column to the left of the text, so the
       picture and the name are read together rather than one after the
       other. Image and body are siblings so CSS can lay them out as a row;
       the body is wrapped so it can be padded without padding the image,
       which runs flush to the popup's edge. */
    var html = "";
    if (site.thumb) {
      html += '<img class="pop-thumb" src="' + site.thumb + '" alt="" loading="lazy">';
    }
    html += '<div class="pop-body">';
    html += "<strong>" + escapeHtml(site.title) + "</strong>";
    if (site.kind) html += '<span class="pop-kind">' + escapeHtml(site.kind) + "</span>";
    if (site.summary) html += '<span class="pop-summary">' + escapeHtml(site.summary) + "</span>";
    if (site.url) html += '<a class="pop-link" href="' + site.url + '">Read the entry →</a>';
    html += "</div>";
    m.bindPopup(html, {
      className: "map-popup",
      maxWidth: 330,
      minWidth: site.thumb ? 300 : 0,
      /* Leaflet pans the map by default so a popup fits. That moves the view
         out from under the reader -- and with hover-to-open it happens on a
         mere pass across a pin near the edge, dragging the map around. The
         popup is clipped by the container's own overflow instead, which is
         the lesser surprise: the map stays where it was put. */
      autoPan: false,
      keepInView: false
    });
    markers.push(m);
    return m;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* Leaflet's default minZoom is 0, which would make a reader scrolling down
     the page zoom a map all the way out to the whole world before
     releaseAtBounds handed the wheel back. Bounding how far out each map can
     go makes the release happen at a sensible point -- and there was never a
     reason to let a map of one church show the Atlantic. */
  var MIN_ZOOM_SINGLE = 11;
  var MIN_ZOOM_OVERVIEW = 5;

  function single(el) {
    var lat = parseFloat(el.dataset.lat);
    var lon = parseFloat(el.dataset.lon);
    if (isNaN(lat) || isNaN(lon)) return;
    var map = L.map(el, Object.assign({ minZoom: MIN_ZOOM_SINGLE }, WHEEL_ZOOM));
    var maxZoom = basemap(el, map);
    map.setView([lat, lon], Math.min(15, maxZoom));
    releaseAtBounds(el, map);
    var one = marker({ lat: lat, lon: lon, title: el.dataset.title || "" }, 8);
    one.addTo(map);
    bindLabel(one, el.dataset.title || "", 8, true);   // one pin never collides
  }

  function overview(el) {
    var map = L.map(el, Object.assign(
      { worldCopyJump: true, minZoom: MIN_ZOOM_OVERVIEW }, WHEEL_ZOOM));
    var maxZoom = basemap(el, map);
    releaseAtBounds(el, map);
    /* A visible default view, so the map is never blank while the fetch is in
       flight or if it fails: the Aegean, which is where the places are. */
    map.setView([38.4, 26.0], 6);

    fetch(el.dataset.src)
      .then(function (r) {
        if (!r.ok) throw new Error("sites.json " + r.status);
        return r.json();
      })
      .then(function (data) {
        var only = el.dataset.region || "";
        var sites = ((data && data.sites) || []).filter(function (s) {
          return !only || s.region === only;
        });
        var byRegion = {};
        var all = [];
        var labelled = [];
        sites.forEach(function (site) {
          var m = marker(site, 7).addTo(map);
          labelled.push({ marker: m, title: site.title, radius: 7 });
          all.push(m.getLatLng());
          (byRegion[site.region] = byRegion[site.region] || []).push(m.getLatLng());
        });
        if (all.length) {
          map.fitBounds(L.latLngBounds(all), { padding: [30, 30], maxZoom: maxZoom });
        }
        followZoom(map, labelled);
        hoverPopups(map, labelled);

        /* The region filter zooms; it does not hide pins. Hiding them would
           lose the point of an overview map, which is seeing how the places
           sit in relation to each other. */
        var figure = el.closest(".map-figure");
        var buttons = figure ? figure.querySelectorAll(".map-filter button") : [];
        buttons.forEach(function (b) {
          b.addEventListener("click", function () {
            buttons.forEach(function (o) { o.classList.toggle("active", o === b); });
            var region = b.dataset.region;
            var pts = region ? byRegion[region] : all;
            if (pts && pts.length) {
              map.fitBounds(L.latLngBounds(pts), {
                padding: [30, 30],
                maxZoom: Math.min(14, maxZoom)
              });
            }
          });
        });
      })
      .catch(function (err) {
        if (window.console) console.warn("[egeria] overview map:", err);
        el.classList.add("map-failed");
      });
  }

  document.querySelectorAll(".map").forEach(function (el) {
    if (el.dataset.map === "overview") overview(el);
    else single(el);
  });
})();
