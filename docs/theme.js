(function () {
  var STORAGE_KEY = "sql-sp-harness-theme";
  var THEMES = ["dark", "light"];

  function preferredTheme() {
    var stored = localStorage.getItem(STORAGE_KEY);
    if (THEMES.indexOf(stored) !== -1) {
      return stored;
    }
    if (window.matchMedia("(prefers-color-scheme: light)").matches) {
      return "light";
    }
    return "dark";
  }

  function syncThemeToggle(theme) {
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) {
      return;
    }
    var isLight = theme === "light";
    toggle.setAttribute("aria-pressed", isLight ? "true" : "false");
    toggle.setAttribute(
      "aria-label",
      isLight ? "Switch to dark theme" : "Switch to light theme"
    );
    toggle.setAttribute(
      "title",
      isLight ? "Switch to dark theme" : "Switch to light theme"
    );
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    syncThemeToggle(theme);
  }

  function initTheme() {
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) {
      return;
    }
    var theme = document.documentElement.getAttribute("data-theme") || preferredTheme();
    if (!document.documentElement.getAttribute("data-theme")) {
      applyTheme(theme);
    } else {
      syncThemeToggle(theme);
    }
    toggle.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme") || "dark";
      applyTheme(current === "dark" ? "light" : "dark");
    });
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", function (event) {
        if (localStorage.getItem(STORAGE_KEY)) {
          return;
        }
        applyTheme(event.matches ? "dark" : "light");
      });
  }

  function initSidebar() {
    var toggle = document.getElementById("menu-toggle");
    var backdrop = document.getElementById("sidebar-backdrop");
    if (!toggle) {
      return;
    }

    function setOpen(open) {
      document.body.classList.toggle("sidebar-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (backdrop) {
        backdrop.setAttribute("aria-hidden", open ? "false" : "true");
      }
    }

    toggle.addEventListener("click", function () {
      setOpen(!document.body.classList.contains("sidebar-open"));
    });

    if (backdrop) {
      backdrop.addEventListener("click", function () {
        setOpen(false);
      });
    }

    document.querySelectorAll(".sidebar-nav a[href^='#']").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.matchMedia("(max-width: 900px)").matches) {
          setOpen(false);
        }
      });
    });
  }

  function boot() {
    initTheme();
    initSidebar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
