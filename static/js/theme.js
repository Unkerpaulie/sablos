/* Lightweight light/dark theme switcher using Bootstrap 5.3 data-bs-theme. */
(function () {
  "use strict";

  const STORAGE_KEY = "sablos-theme";
  const html = document.documentElement;

  function preferredTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function applyTheme(theme) {
    html.setAttribute("data-bs-theme", theme);
    document.querySelectorAll("[data-theme-icon-light]").forEach((el) => {
      el.classList.toggle("d-none", theme === "dark");
    });
    document.querySelectorAll("[data-theme-icon-dark]").forEach((el) => {
      el.classList.toggle("d-none", theme === "light");
    });
  }

  function toggleTheme() {
    const next = html.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, next);
    applyTheme(next);
  }

  applyTheme(preferredTheme());

  document.addEventListener("click", function (event) {
    const target = event.target.closest("[data-theme-toggle]");
    if (target) {
      event.preventDefault();
      toggleTheme();
    }
  });
})();
