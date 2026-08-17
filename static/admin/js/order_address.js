(function () {
  "use strict";

  function autosize(el) {
    if (!el || el.tagName !== "TEXTAREA") return;
    el.style.height = "auto";
    el.style.height = Math.max(el.scrollHeight, 56) + "px";
  }

  function wireAddressAutosize() {
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

  var STATUS_PREFIX = "order-row-";

  function clearStatusClasses(tr) {
    if (!tr || !tr.classList) return;
    Array.prototype.slice.call(tr.classList).forEach(function (cls) {
      if (cls.indexOf(STATUS_PREFIX) === 0) tr.classList.remove(cls);
    });
  }

  function applyStatusStyles(select) {
    if (!select) return;
    var value = (select.value || "").trim();
    select.setAttribute("data-status", value);
    var tr = select.closest("tr");
    if (!tr) return;
    clearStatusClasses(tr);
    if (value) tr.classList.add(STATUS_PREFIX + value);
  }

  function wireOrderStatusColors() {
    var table = document.getElementById("result_list");
    if (!table) return;
    table.querySelectorAll("td.field-status select").forEach(function (select) {
      applyStatusStyles(select);
      if (select.dataset.statusWired) return;
      select.dataset.statusWired = "1";
      select.addEventListener("change", function () {
        applyStatusStyles(select);
      });
    });
  }

  function wire() {
    wireAddressAutosize();
    wireOrderStatusColors();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();
