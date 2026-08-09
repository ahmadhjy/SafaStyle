(function () {
  "use strict";

  function autosize(el) {
    if (!el || el.tagName !== "TEXTAREA") return;
    el.style.height = "auto";
    el.style.height = Math.max(el.scrollHeight, 56) + "px";
  }

  function wire() {
    document.querySelectorAll("textarea.order-address-field").forEach(function (el) {
      if (el.dataset.autosizeWired) {
        autosize(el);
        return;
      }
      el.dataset.autosizeWired = "1";
      el.addEventListener("input", function () {
        autosize(el);
      });
      autosize(el);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();
