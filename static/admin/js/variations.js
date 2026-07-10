/* Variations tab helpers for the Product admin:
 *  - "Generate variations" button that builds the color×size matrix on the spot
 *  - a bulk editor to set the same price / sale price / stock on every row
 */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  function getCookie(name) {
    var m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? m.pop() : "";
  }

  function findPrefix() {
    // Django always renders an empty "template" row we can read the prefix from.
    var tmpl = document.querySelector('[name$="-__prefix__-stock"]');
    return tmpl ? tmpl.getAttribute("name").split("-__prefix__-")[0] : null;
  }

  function findGroup(prefix) {
    if (prefix) {
      var g = document.getElementById(prefix + "-group");
      if (g) return g;
    }
    var groups = document.querySelectorAll(".inline-group");
    for (var i = 0; i < groups.length; i++) {
      if (groups[i].querySelector('[name*="stock"]')) return groups[i];
    }
    return null;
  }

  function rowInputs(group, suffix) {
    var out = [];
    var els = group.querySelectorAll('[name$="-' + suffix + '"]');
    for (var i = 0; i < els.length; i++) {
      // numbered rows only — skip the __prefix__ template row
      if (/-\d+-/.test(els[i].getAttribute("name"))) out.push(els[i]);
    }
    return out;
  }

  ready(function () {
    var prefix = findPrefix();
    var group = findGroup(prefix);
    if (!group) return;

    var pid = null;
    var m = window.location.pathname.match(/\/(\d+)\/change\/?$/);
    if (m) pid = m[1];

    var bar = document.createElement("div");
    bar.className = "ss-var-toolbar";
    bar.innerHTML =
      '<div class="ss-var-row">' +
      '  <button type="button" class="button ss-var-generate">&#9881; Generate variations</button>' +
      '  <span class="ss-var-hint">Builds every color &times; size combination from the ' +
      "     Colors &amp; sizes you saved. Existing rows are kept.</span>" +
      "</div>" +
      '<div class="ss-var-row ss-var-bulk">' +
      "  <strong>Bulk edit:</strong>" +
      '  <label>Price <input type="number" step="0.01" min="0" data-bulk="price"></label>' +
      '  <label>Sale <input type="number" step="0.01" min="0" data-bulk="sale_price"></label>' +
      '  <label>Stock <input type="number" step="1" min="0" data-bulk="stock"></label>' +
      '  <button type="button" class="button ss-var-apply">Apply to all rows</button>' +
      '  <span class="ss-var-hint" data-role="msg"></span>' +
      "</div>";
    group.insertBefore(bar, group.firstChild);

    // --- Generate ---------------------------------------------------------
    var genBtn = bar.querySelector(".ss-var-generate");
    genBtn.addEventListener("click", function () {
      if (!pid) {
        alert("Please save the product first, then generate variations.");
        return;
      }
      if (
        !confirm(
          "Generate variations for every saved color \u00d7 size combination?\n\n" +
            "This reloads the page — save any other edits first."
        )
      )
        return;
      genBtn.disabled = true;
      genBtn.innerHTML = "Generating\u2026";
      var url = window.location.pathname.replace(
        /\/change\/?$/,
        "/generate-variations/"
      );
      fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (d) {
          if (d && d.ok) {
            window.location.reload();
          } else {
            alert((d && d.error) || "Could not generate variations.");
            genBtn.disabled = false;
            genBtn.innerHTML = "&#9881; Generate variations";
          }
        })
        .catch(function () {
          alert("Network error while generating variations.");
          genBtn.disabled = false;
          genBtn.innerHTML = "&#9881; Generate variations";
        });
    });

    // --- Bulk apply (client-side; fills the form, then user Saves) ---------
    var applyBtn = bar.querySelector(".ss-var-apply");
    var msg = bar.querySelector('[data-role="msg"]');
    applyBtn.addEventListener("click", function () {
      var applied = 0;
      ["price", "sale_price", "stock"].forEach(function (suffix) {
        var field = bar.querySelector('[data-bulk="' + suffix + '"]');
        if (!field || field.value === "") return;
        rowInputs(group, suffix).forEach(function (inp) {
          inp.value = field.value;
          applied++;
        });
      });
      msg.textContent = applied
        ? "Filled " + applied + " field(s). Click Save to keep the changes."
        : "Enter a price, sale price or stock value first.";
    });
  });
})();
