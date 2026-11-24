// Mobile menu: one button toggles the dropdown. Closes on Escape, on an outside tap, on a link
// tap, and when the window grows past the mobile breakpoint. No dependencies.
(function () {
  "use strict";
  var btn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  if (!btn || !nav) return;
  function set(open) {
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.querySelector(".txt").textContent = open ? "Close" : "Menu";
    nav.classList.toggle("open", open);
  }
  btn.addEventListener("click", function () { set(btn.getAttribute("aria-expanded") !== "true"); });
  nav.addEventListener("click", function (e) { if (e.target.closest("a")) set(false); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && nav.classList.contains("open")) { set(false); btn.focus(); }
  });
  document.addEventListener("click", function (e) {
    if (nav.classList.contains("open") && !nav.contains(e.target) && !btn.contains(e.target)) set(false);
  });
  window.matchMedia("(min-width: 861px)").addEventListener("change", function (m) { if (m.matches) set(false); });
})();
