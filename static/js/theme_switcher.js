// theme_switcher.js
// Cosmetic only: 3 themes (classic/warm/midnight). Persists in localStorage.

(function () {
  var STORAGE_KEY = "skylane_theme";
  var DEFAULT_THEME = "classic";
  var THEMES = ["classic", "warm", "midnight"];

  function applyTheme(theme) {
    var t = THEMES.includes(theme) ? theme : DEFAULT_THEME;
    document.documentElement.setAttribute("data-theme", t);

    // update active state
    var items = document.querySelectorAll(".theme-switcher__item");
    items.forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-theme") === t);
    });

    try { localStorage.setItem(STORAGE_KEY, t); } catch (e) {}
  }

  function loadTheme() {
    var t = null;
    try { t = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    return t || DEFAULT_THEME;
  }

  function closePanel(switcher) {
    switcher.classList.remove("is-open");
    var toggle = document.getElementById("themeToggle");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
    var panel = document.getElementById("themePanel");
    if (panel) panel.setAttribute("aria-hidden", "true");
  }

  function openPanel(switcher) {
    switcher.classList.add("is-open");
    var toggle = document.getElementById("themeToggle");
    if (toggle) toggle.setAttribute("aria-expanded", "true");
    var panel = document.getElementById("themePanel");
    if (panel) panel.setAttribute("aria-hidden", "false");
  }

  function init() {
    var switcher = document.getElementById("themeSwitcher");
    if (!switcher) return;

    // initial theme
    applyTheme(loadTheme());

    var toggle = document.getElementById("themeToggle");
    if (toggle) {
      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        if (switcher.classList.contains("is-open")) closePanel(switcher);
        else openPanel(switcher);
      });
    }

    // buttons
    switcher.querySelectorAll(".theme-switcher__item").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        applyTheme(btn.getAttribute("data-theme"));
        closePanel(switcher);
      });
    });

    // click-away close
    document.addEventListener("click", function (e) {
      if (!switcher.contains(e.target)) closePanel(switcher);
    });

    // Esc close
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closePanel(switcher);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
