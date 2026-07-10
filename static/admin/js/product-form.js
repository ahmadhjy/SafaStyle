/* Prevent duplicate product creation from double-clicks on Save. */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var form = document.querySelector("#product_form");
    if (!form) return;

    var submitting = false;
    form.addEventListener(
      "submit",
      function (e) {
        if (submitting) {
          e.preventDefault();
          return;
        }
        submitting = true;
        form.querySelectorAll('input[type="submit"], button[type="submit"]').forEach(function (btn) {
          btn.disabled = true;
          if (btn.tagName === "INPUT") btn.value = "Saving…";
          else btn.textContent = "Saving…";
        });
      },
      true
    );
  });
})();
