(() => {
  "use strict";

  const form = document.getElementById("checkout-form");
  if (!form) return;

  const countryEl = document.getElementById("id_country");
  const govField = document.getElementById("governorate-field");
  const govEl = document.getElementById("id_governorate");
  const cityField = document.getElementById("city-field");
  const cityEl = document.getElementById("id_city");
  const localityField = document.getElementById("locality-field");
  const localityIdEl = form.querySelector("[data-locality-id]");
  const searchEl = form.querySelector("[data-locality-search]");
  const listEl = form.querySelector("[data-locality-list]");
  const deliveryLine = document.getElementById("delivery-line");
  const deliveryAmount = document.getElementById("delivery-amount");
  const totalEl = document.getElementById("checkout-total");
  const subtotal = Number(window.CHECKOUT_SUBTOTAL || 0);

  let governorates = [];
  let localities = [];
  try {
    governorates = JSON.parse(
      document.getElementById("checkout-governorates").textContent
    );
  } catch (e) {
    governorates = [];
  }
  try {
    localities = JSON.parse(
      document.getElementById("checkout-localities").textContent
    );
  } catch (e) {
    localities = [];
  }

  const feeById = {};
  const govNameById = {};
  governorates.forEach((g) => {
    feeById[String(g.id)] = Number(g.delivery_fee);
    govNameById[String(g.id)] = g.name;
  });

  const localityById = {};
  localities.forEach((loc) => {
    localityById[String(loc.id)] = loc;
  });

  let highlightIndex = -1;
  let filtered = [];

  function isLebanon() {
    return countryEl && countryEl.value === "Lebanon";
  }

  function setGovernorate(govId, { silent } = {}) {
    if (!govEl) return;
    const value = govId ? String(govId) : "";
    if (govEl.value !== value) {
      govEl.value = value;
      if (!silent) {
        govEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
    // Keep fee zone locked to the selected town — customers cannot override it.
    govEl.disabled = isLebanon() && !!value;
  }

  function updateTotals() {
    let delivery = 0;
    if (isLebanon() && govEl && govEl.value) {
      delivery = feeById[govEl.value] || 0;
    }
    if (deliveryLine && deliveryAmount) {
      if (delivery > 0) {
        deliveryLine.hidden = false;
        deliveryAmount.textContent = `$${delivery.toFixed(2)}`;
      } else {
        deliveryLine.hidden = true;
      }
    }
    if (totalEl) {
      totalEl.textContent = `$${(subtotal + delivery).toFixed(2)}`;
    }
  }

  function closeList() {
    if (!listEl || !searchEl) return;
    listEl.hidden = true;
    listEl.innerHTML = "";
    searchEl.setAttribute("aria-expanded", "false");
    highlightIndex = -1;
  }

  function openList() {
    if (!listEl || !searchEl) return;
    listEl.hidden = false;
    searchEl.setAttribute("aria-expanded", "true");
  }

  function renderList(items) {
    if (!listEl) return;
    filtered = items;
    highlightIndex = items.length ? 0 : -1;
    if (!items.length) {
      listEl.innerHTML =
        '<li class="locality-empty" role="presentation">No matching town found</li>';
      openList();
      return;
    }
    listEl.innerHTML = items
      .map((loc, i) => {
        const gov = govNameById[String(loc.governorate_id)] || "";
        return (
          `<li role="option" tabindex="-1" data-id="${loc.id}"` +
          ` class="locality-option${i === 0 ? " is-active" : ""}"` +
          ` aria-selected="${i === 0 ? "true" : "false"}">` +
          `<span class="locality-name">${escapeHtml(loc.name)}</span>` +
          `<span class="locality-gov">${escapeHtml(gov)}</span>` +
          `</li>`
        );
      })
      .join("");
    openList();
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function filterLocalities(query) {
    const q = (query || "").trim().toLowerCase();
    if (!q) {
      // Show a helpful starter set alphabetically.
      return localities.slice().sort((a, b) => a.name.localeCompare(b.name)).slice(0, 40);
    }
    const starts = [];
    const contains = [];
    localities.forEach((loc) => {
      const name = loc.name.toLowerCase();
      if (name.startsWith(q)) starts.push(loc);
      else if (name.includes(q)) contains.push(loc);
    });
    starts.sort((a, b) => a.name.localeCompare(b.name));
    contains.sort((a, b) => a.name.localeCompare(b.name));
    return starts.concat(contains).slice(0, 60);
  }

  function selectLocality(loc) {
    if (!loc) return;
    if (localityIdEl) localityIdEl.value = String(loc.id);
    if (searchEl) searchEl.value = loc.name;
    if (cityEl) cityEl.value = loc.name;
    setGovernorate(loc.governorate_id);
    updateTotals();
    closeList();
  }

  function clearLocality() {
    if (localityIdEl) localityIdEl.value = "";
    if (isLebanon() && cityEl) cityEl.value = "";
    setGovernorate("");
    updateTotals();
  }

  function syncCountryFields() {
    const lebanon = isLebanon();
    if (localityField) localityField.hidden = !lebanon;
    if (govField) govField.hidden = !lebanon;
    if (cityField) cityField.hidden = lebanon;

    if (!lebanon) {
      closeList();
      if (localityIdEl) localityIdEl.value = "";
      if (searchEl) searchEl.value = "";
      setGovernorate("");
      if (govEl) {
        govEl.disabled = false;
        govEl.required = false;
      }
      if (cityEl) cityEl.required = true;
    } else {
      if (cityEl) cityEl.required = false;
      if (govEl) govEl.required = false;
      // Re-apply locality → governorate if already chosen.
      const selected = localityIdEl && localityById[localityIdEl.value];
      if (selected) {
        selectLocality(selected);
      } else {
        setGovernorate(govEl ? govEl.value : "");
      }
    }
    updateTotals();
  }

  // Restore selected locality label after validation errors.
  if (localityIdEl && localityIdEl.value && searchEl) {
    const existing = localityById[localityIdEl.value];
    if (existing) {
      searchEl.value = existing.name;
      if (cityEl) cityEl.value = existing.name;
    }
  }

  searchEl?.addEventListener("focus", () => {
    if (!isLebanon()) return;
    renderList(filterLocalities(searchEl.value));
  });

  searchEl?.addEventListener("input", () => {
    if (!isLebanon()) return;
    const current = localityIdEl && localityById[localityIdEl.value];
    if (!current || current.name !== searchEl.value.trim()) {
      // Typing again invalidates a previous pick until they re-select.
      if (localityIdEl) localityIdEl.value = "";
      setGovernorate("");
      updateTotals();
    }
    renderList(filterLocalities(searchEl.value));
  });

  searchEl?.addEventListener("keydown", (e) => {
    if (!isLebanon() || !listEl || listEl.hidden) {
      if (e.key === "ArrowDown") {
        renderList(filterLocalities(searchEl.value));
      }
      return;
    }
    const options = Array.from(listEl.querySelectorAll(".locality-option"));
    if (!options.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      highlightIndex = Math.min(options.length - 1, highlightIndex + 1);
      options.forEach((opt, i) => {
        opt.classList.toggle("is-active", i === highlightIndex);
        opt.setAttribute("aria-selected", i === highlightIndex ? "true" : "false");
      });
      options[highlightIndex]?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      highlightIndex = Math.max(0, highlightIndex - 1);
      options.forEach((opt, i) => {
        opt.classList.toggle("is-active", i === highlightIndex);
        opt.setAttribute("aria-selected", i === highlightIndex ? "true" : "false");
      });
      options[highlightIndex]?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
      e.preventDefault();
      const opt = options[highlightIndex] || options[0];
      const loc = localityById[opt?.dataset.id];
      if (loc) selectLocality(loc);
    } else if (e.key === "Escape") {
      closeList();
    }
  });

  listEl?.addEventListener("mousedown", (e) => {
    const opt = e.target.closest(".locality-option");
    if (!opt) return;
    e.preventDefault();
    const loc = localityById[opt.dataset.id];
    if (loc) selectLocality(loc);
  });

  document.addEventListener("click", (e) => {
    if (!localityField || localityField.hidden) return;
    if (!localityField.contains(e.target)) closeList();
  });

  countryEl?.addEventListener("change", syncCountryFields);
  govEl?.addEventListener("change", updateTotals);

  // Prevent duplicate orders from double-clicks / impatient resubmits.
  const placeBtn = form.querySelector("[data-place-order]");
  let submitting = false;
  form.addEventListener("submit", (e) => {
    // Re-enable disabled governorate so its value is included in the POST.
    if (govEl && govEl.disabled) {
      govEl.disabled = false;
    }

    if (isLebanon()) {
      const loc = localityIdEl && localityById[localityIdEl.value];
      if (!loc) {
        e.preventDefault();
        submitting = false;
        if (placeBtn) {
          placeBtn.disabled = false;
          placeBtn.textContent = placeBtn.dataset.label || "Place order";
        }
        if (searchEl) {
          searchEl.focus();
          renderList(filterLocalities(searchEl.value));
        }
        return;
      }
      // Ensure city + governorate match the locked locality before submit.
      if (cityEl) cityEl.value = loc.name;
      setGovernorate(loc.governorate_id, { silent: true });
      if (govEl) govEl.disabled = false;
    }

    if (submitting) {
      e.preventDefault();
      return;
    }
    submitting = true;
    if (placeBtn) {
      placeBtn.disabled = true;
      placeBtn.dataset.label = placeBtn.textContent;
      placeBtn.textContent = "Placing your order…";
    }
  });

  syncCountryFields();
})();
