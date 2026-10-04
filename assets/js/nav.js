/* Left-menu behaviour: the drawer on narrow viewports, and remembering which
   region disclosures the reader left open.

   localStorage is wrapped in try/catch everywhere -- it throws in a private
   window and with site data blocked, and the menu must work regardless. It is
   used only for this convenience; nothing here is state the site depends on. */
(function () {
  "use strict";

  var KEY = "egeria.openRegions";
  var sidebar = document.getElementById("sidebar");
  var toggle = document.getElementById("menu-toggle");
  var backdrop = document.querySelector(".sidebar-backdrop");
  if (!sidebar) return;

  /* ---- the drawer ---- */

  function setOpen(open) {
    sidebar.classList.toggle("open", open);
    document.body.classList.toggle("menu-open", open);
    if (backdrop) backdrop.hidden = !open;
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      setOpen(!sidebar.classList.contains("open"));
    });
  }
  if (backdrop) backdrop.addEventListener("click", function () { setOpen(false); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setOpen(false);
  });
  /* Following a link inside the drawer navigates; close it so the drawer is
     not still open behind the new page on a browser that restores state. */
  sidebar.addEventListener("click", function (e) {
    if (e.target.closest("a")) setOpen(false);
  });

  /* ---- remembered disclosures ---- */

  var regions = sidebar.querySelectorAll("details.sidebar-region");

  function read() {
    try {
      var raw = window.localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function save() {
    var open = [];
    regions.forEach(function (d) {
      if (d.open) open.push(d.dataset.region);
    });
    try {
      window.localStorage.setItem(KEY, JSON.stringify(open));
    } catch (e) { /* nothing to do; the menu still works */ }
  }

  var remembered = read();
  if (remembered) {
    regions.forEach(function (d) {
      /* The region of the page being viewed is always open, whatever was
         remembered -- otherwise you land on an entry whose own region is
         collapsed, which reads as a broken menu. */
      if (d.hasAttribute("open")) return;
      d.open = remembered.indexOf(d.dataset.region) !== -1;
    });
  }
  regions.forEach(function (d) { d.addEventListener("toggle", save); });

  /* Scroll the menu so the current entry is visible. Instant, not smooth:
     smooth scrolling on a container silently no-ops often enough that it
     cannot be relied on. */
  var current = sidebar.querySelector("a.current");
  if (current) {
    var top = current.offsetTop - sidebar.clientHeight / 2;
    if (top > 0) sidebar.scrollTop = top;
  }
})();
