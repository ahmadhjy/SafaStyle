(() => {
  "use strict";

  const form = document.getElementById("checkout-form");
  if (!form) return;

  const countryEl = document.getElementById("id_country");
  const govField = document.getElementById("governorate-field");
  const govEl = document.getElementById("id_governorate");
  const deliveryLine = document.getElementById("delivery-line");
  const deliveryAmount = document.getElementById("delivery-amount");
  const totalEl = document.getElementById("checkout-total");
  const subtotal = Number(window.CHECKOUT_SUBTOTAL || 0);

  let governorates = [];
  try {
    governorates = JSON.parse(
      document.getElementById("checkout-governorates").textContent
    );
  } catch (e) {
    governorates = [];
  }

  const feeById = {};
  governorates.forEach((g) => {
    feeById[String(g.id)] = Number(g.delivery_fee);
  });

  function isLebanon() {
    return countryEl && countryEl.value === "Lebanon";
  }

  function syncGovernorateField() {
    if (!govField || !govEl) return;
    const show = isLebanon();
    govField.hidden = !show;
    govEl.required = show;
    if (!show) {
      govEl.value = "";
    }
    updateTotals();
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

  countryEl?.addEventListener("change", syncGovernorateField);
  govEl?.addEventListener("change", updateTotals);

  // Prevent duplicate orders from double-clicks / impatient resubmits.
  const placeBtn = form.querySelector("[data-place-order]");
  let submitting = false;
  form.addEventListener("submit", (e) => {
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

  syncGovernorateField();
})();
