/* Product admin — prevent double-save and warn on unsaved changes. */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  function formSnapshot(form) {
    var parts = [];
    form.querySelectorAll("input, select, textarea").forEach(function (el) {
      if (!el.name || el.type === "submit" || el.type === "button") return;
      if (el.type === "checkbox" || el.type === "radio") {
        parts.push(el.name + "=" + (el.checked ? el.value : ""));
      } else if (el.type !== "file") {
        parts.push(el.name + "=" + el.value);
      }
    });
    return parts.join("|");
  }

  function isSaveAction(target) {
    if (!target) return false;
    if (target.closest(".submit-row")) return true;
    if (target.matches('input[type="submit"], button[type="submit"]')) return true;
    var name = (target.getAttribute("name") || "").toLowerCase();
    return name === "_save" || name === "_continue" || name === "_addanother";
  }

  ready(function () {
    var form = document.querySelector("#product_form");
    if (!form) return;

    var submitting = false;
    var allowLeave = false;
    var initialSnapshot = "";

    setTimeout(function () {
      initialSnapshot = formSnapshot(form);
    }, 400);

    function isDirty() {
      if (!initialSnapshot) return false;
      return !allowLeave && formSnapshot(form) !== initialSnapshot;
    }

    form.addEventListener(
      "submit",
      function (e) {
        if (submitting) {
          e.preventDefault();
          return;
        }
        submitting = true;
        allowLeave = true;
        form.querySelectorAll('input[type="submit"], button[type="submit"]').forEach(function (btn) {
          btn.disabled = true;
          if (btn.tagName === "INPUT") btn.value = "Saving…";
          else btn.textContent = "Saving…";
        });
      },
      true
    );

    window.addEventListener("beforeunload", function (e) {
      if (!isDirty()) return;
      e.preventDefault();
      e.returnValue = "";
    });

    document.addEventListener(
      "click",
      function (e) {
        if (!isDirty() || isSaveAction(e.target)) return;

        var link = e.target.closest("a[href]");
        if (!link) return;
        if (link.target === "_blank" || e.metaKey || e.ctrlKey || e.shiftKey) return;

        var href = link.getAttribute("href") || "";
        if (!href || href.charAt(0) === "#") return;
        if (link.closest("#product_form")) return;

        if (
          !window.confirm(
            "You have unsaved changes on this product. Leave without saving?"
          )
        ) {
          e.preventDefault();
          e.stopPropagation();
        } else {
          allowLeave = true;
        }
      },
      true
    );
  });
})();
