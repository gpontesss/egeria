/* Theme: follows the operating system until the reader picks one, then
   remembers the choice. This script is INLINED in <head> (see head.html) and
   must stay small, because it has to run before first paint -- applying the
   stored theme from a deferred script would show a flash of the wrong one.

   localStorage is wrapped in try/catch throughout: it throws in a private
   window and with site data blocked, and the site must work regardless. With
   no storage the theme simply follows the system, which is the default
   anyway. */
(function () {
  "use strict";

  var KEY = "egeria.theme";
  var root = document.documentElement;

  function stored() {
    try {
      var v = window.localStorage.getItem(KEY);
      return v === "dark" || v === "light" ? v : null;
    } catch (e) {
      return null;
    }
  }

  function system() {
    return window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function resolved() {
    return stored() || system();
  }

  /* Before paint: if the reader has chosen, honour it. If not, the attribute
     stays off and style.css's prefers-color-scheme query decides. */
  var chosen = stored();
  if (chosen) root.setAttribute("data-theme", chosen);

  /* The maps draw their markers in the text colour and invert their tiles, so
     they need telling when the theme changes under them. */
  function announce() {
    document.dispatchEvent(
      new CustomEvent("egeria:theme", { detail: { theme: resolved() } })
    );
  }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;

    function sync() {
      var now = resolved();
      btn.dataset.resolved = now;
      btn.setAttribute(
        "aria-label",
        now === "dark" ? "Switch to the light theme" : "Switch to the dark theme"
      );
    }

    sync();
    /* Revealed only now: the button is useless without this script, so it
       ships hidden rather than sitting there inert for a reader with JS off. */
    btn.hidden = false;

    btn.addEventListener("click", function () {
      var next = resolved() === "dark" ? "light" : "dark";
      try {
        window.localStorage.setItem(KEY, next);
      } catch (e) { /* the toggle still works for this page */ }
      root.setAttribute("data-theme", next);
      sync();
      announce();
    });

    if (window.matchMedia) {
      window
        .matchMedia("(prefers-color-scheme: dark)")
        .addEventListener("change", function () {
          if (!stored()) {
            sync();
            announce();
          }
        });
    }
  });
})();
